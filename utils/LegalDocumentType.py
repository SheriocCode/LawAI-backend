from enum import Enum

class LegalDocumentType(Enum):
    LAWS = "法律法规"
    JUDICIAL_CASES = "司法案例"
    JUDGMENT_DOCUMENTS = "裁判文书"
    BUSINESS_FILES = "业务文件"
    LITIGATION_GUIDES = "诉讼指南"

class LegalDocumentType_Min(Enum):
    laws = "法律法规"
    judicial_cases = "司法案例"
    judgment_documents = "裁判文书"
    business_files = "业务文件"
    litigation_guides = "诉讼指南"

# 使用示例
type = LegalDocumentType.LAWS_AND_REGULATIONS
print(f"当前文档类型：{type.value}")