import zipfile
import os
import json
from lxml import etree
import re

class DocxExtractor:
    symbol_font_map = {
        "F000": "∀", "F001": "∂", "F002": "∃", "F003": "∅",
        "F070": "π", "F06E": "φ", "F06C": "μ", "F071": "∇",
        "F03A": "≥", "F03C": "≤", "F05C": "∑", "F0D0": "√",
        "F04D": "∞", "F07E": "≠"
        # Add more if needed
    }

    def __init__(self, temp_dir="_docx_extract_temp"):
        self.temp_dir = temp_dir

    def extract(self, docx_path, as_string=True):
        xml_path = self._unzip_docx(docx_path)
        content = self._parse_document_xml_ordered(xml_path)
        rels_path = os.path.join(self.temp_dir, "word", "_rels", "document.xml.rels")
        rel_map = self._map_rids_to_paths(rels_path)
        content = self._attach_paths_to_images(content, rel_map)
        if as_string:
            return self._flatten_content(content)
        else:
            return content

    def _unzip_docx(self, docx_path):
        os.makedirs(self.temp_dir, exist_ok=True)
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        return os.path.join(self.temp_dir, "word", "document.xml")

    def _parse_document_xml_ordered(self, xml_path):
        with open(xml_path, "rb") as f:
            tree = etree.parse(f)
        ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "v": "urn:schemas-microsoft-com:vml",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture"
        }
        content = []
        for p in tree.xpath("//w:body/w:p", namespaces=ns):
            para_bold = False
            pPr = p.find("w:pPr", namespaces=ns)
            if pPr is not None:
                para_rPr = pPr.find("w:rPr", namespaces=ns)
                if para_rPr is not None and para_rPr.find("w:b", namespaces=ns) is not None:
                    para_bold = True
            for run in p.xpath(".//w:r", namespaces=ns):
                run_bold = para_bold
                rpr = run.find("w:rPr", namespaces=ns)
                if rpr is not None and rpr.find("w:b", namespaces=ns) is not None:
                    run_bold = True
                for node in run.iter():
                    tag = etree.QName(node).localname
                    if tag == "t":
                        txt = node.text.strip() if node.text else ""
                        if txt:
                            content.append({"type": "text", "content": txt, "is_bold": run_bold})
                    elif tag == "imagedata":
                        rId = node.attrib.get(f"{{{ns['r']}}}id")
                        if rId:
                            content.append({"type": "image", "rId": rId})
                    elif tag == "blip":
                        rId = node.attrib.get(f"{{{ns['r']}}}embed")
                        if rId:
                            content.append({"type": "image", "rId": rId})
                    elif tag == "sym":
                        hex_code = node.attrib.get(f"{{{ns['w']}}}char") or node.attrib.get("w:char")
                        if hex_code:
                            char = self.symbol_font_map.get(hex_code.upper(), None)
                            if char:
                                content.append({"type": "text", "content": char, "is_bold": run_bold})
                            else:
                                try:
                                    content.append({"type": "text", "content": chr(int(hex_code, 16)), "is_bold": run_bold})
                                except:
                                    pass
        return content

    def _map_rids_to_paths(self, rels_path):
        tree = etree.parse(rels_path)
        root = tree.getroot()
        ns_uri = "http://schemas.openxmlformats.org/package/2006/relationships"
        rel_map = {}
        for rel in root.findall(f"{{{ns_uri}}}Relationship"):
            rId = rel.attrib.get("Id")
            target = rel.attrib.get("Target")
            rel_type = rel.attrib.get("Type", "")
            if "image" in rel_type and target.startswith("media/") and any(
                target.endswith(ext) for ext in [".wmf", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".wdp"]
            ):
                rel_map[rId] = os.path.join(self.temp_dir, "word", target)
        return rel_map

    def _attach_paths_to_images(self, content_list, rel_map):
        for item in content_list:
            if item.get("type") == "image" and "rId" in item:
                rId = item["rId"]
                item["path"] = rel_map.get(rId)
        return content_list

    def _flatten_content(self, content_list):
        parts = []
        for item in content_list:
            if item["type"] == "text":
                parts.append(item["content"])
            elif item["type"] == "image":
                parts.append(f"[IMAGE: {item.get('path', 'unknown')}]")
        return " ".join(parts)

# Example usage (not run on import):
# extractor = DocxExtractor()
# result = extractor.extract("yourfile.docx", as_string=True)
# print(result)
