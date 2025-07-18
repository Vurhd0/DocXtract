from DocXtract import DocxExtractor


extractor = DocxExtractor()
data = extractor.extract("EoI_HairSalonServices.docx")
print(data)