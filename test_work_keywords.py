#!/usr/bin/env python3
"""
Test work experience keyword extraction functionality
"""

import sys
import os

# 添加api目录到路径
api_path = os.path.join(os.path.dirname(__file__), 'api')
sys.path.insert(0, api_path)

# 直接复制函数，避免导入问题


def extract_work_experience_keywords(cv_text: str) -> str:
    """
    从CV文本中提取工作经历相关的关键词
    """
    import re

    # 工作经历相关的关键词模式
    work_patterns = [
        # 英文关键词
        r'\b(?:work|working|worked|employment|employed|job|position|role|career)\b',
        r'\b(?:experience|experiences|professional|occupation|industry)\b',
        r'\b(?:company|corporation|firm|organization|startup|enterprise)\b',
        r'\b(?:manager|developer|engineer|analyst|consultant|specialist|director)\b',
        r'\b(?:intern|internship|volunteer|project|team|lead|senior|junior)\b',

        # 中文关键词
        r'(?:工作|就业|职业|岗位|职位|角色|经历)',
        r'(?:公司|企业|机构|组织|团队|部门)',
        r'(?:经理|开发|工程师|分析师|顾问|专家|主管)',
        r'(?:实习|项目|负责|参与|管理|领导)',
    ]

    extracted_keywords = set()
    cv_text_lower = cv_text.lower()

    # 提取匹配的关键词
    for pattern in work_patterns:
        matches = re.findall(pattern, cv_text_lower, re.IGNORECASE)
        extracted_keywords.update(matches)

    # 额外提取工作相关的专有名词 (公司名、技术栈等)
    # 寻找可能的公司名 (大写字母开头的词)
    company_pattern = r'\b[A-Z][a-zA-Z]{2,}\s*(?:Inc|Corp|Ltd|LLC|Technology|Tech|Software|Systems|Solutions|Group|Company)?\b'
    company_matches = re.findall(company_pattern, cv_text)

    # 技术相关关键词
    tech_patterns = [
        r'\b(?:Python|Java|JavaScript|C\+\+|React|Node\.js|SQL|AWS|Azure|Docker)\b',
        r'\b(?:machine learning|artificial intelligence|data science|backend|frontend)\b',
        r'\b(?:agile|scrum|git|github|database|API|microservices|cloud)\b'
    ]

    for pattern in tech_patterns:
        tech_matches = re.findall(pattern, cv_text, re.IGNORECASE)
        extracted_keywords.update([match.lower() for match in tech_matches])

    # 限制关键词数量，避免query过长
    keywords_list = list(extracted_keywords)[:10]  # 最多10个关键词

    return ' '.join(keywords_list)


def test_work_keywords_extraction():
    """Test work experience keyword extraction"""

    # Test样本CV文本
    sample_cv = """
    PROFESSIONAL SUMMARY
    AI & Software Development | Master of IT (Mar 2026) | Bridging business and technology
    
    WORK EXPERIENCE
    Intelligence Engineer Intern                     Jun. 2022 - Aug. 2022
    Technology Company, Beijing
    • Executed 4+ ML projects spanning bioinformatics
    • Worked with Python, JavaScript, and machine learning
    • Developed backend APIs using Node.js
    • Collaborated with team of 5 engineers
    
    Software Developer                              Jan. 2021 - May 2022  
    Startup Inc, Shanghai
    • Built web applications using React and SQL
    • Managed database systems and cloud infrastructure
    • Led agile development process
    
    项目经历：
    人工智能项目负责人                              2020years9月 - 2021years12月
    • 负责机器学习模型开发
    • 参与团队管理和技术决策
    • 使用AWS云服务部署系统
    """

    print("🔍 Test work experience keyword extraction...")
    print("=" * 50)

    keywords = extract_work_experience_keywords(sample_cv)

    print(f"📝 Original CV snippet:")
    print(sample_cv[:200] + "...")
    print()

    print(f"🎯 Extracted work keywords:")
    print(f"'{keywords}'")
    print()

    # 分析关键词
    keyword_list = keywords.split() if keywords else []
    print(f"📊 Keyword analysis:")
    print(f"- 总数: {len(keyword_list)}")
    print(f"- 详细列表: {keyword_list}")
    print()

    # 验证预期关键词是否被提取
    expected_keywords = [
        'professional', 'work', 'experience', 'engineer', 'intern',
        'developer', 'company', 'team', 'project', 'python',
        'javascript', 'machine', 'learning', 'backend', 'react'
    ]

    found_keywords = []
    for expected in expected_keywords:
        if expected in keyword_list:
            found_keywords.append(expected)

    print(f"✅ Successfully extracted expected keywords: {found_keywords}")
    print(f"📈 Extraction success rate: {len(found_keywords)}/{len(expected_keywords)} ({len(found_keywords)/len(expected_keywords)*100:.1f}%)")

    return keywords


def test_query_enhancement():
    """Test query enhancement effect"""

    print("\n" + "=" * 50)
    print("🚀 Test query enhancement effect...")

    # 模拟候选人数据
    candidate_data = {
        'bachelor_major': 'computer science',
        'interests': ['machine learning', 'artificial intelligence']
    }

    # Original query
    base_query = f"{candidate_data['bachelor_major']} {' '.join(candidate_data['interests'])}"
    print(f"📝 Original query: '{base_query}'")

    # 提取工作关键词
    sample_cv = """
    Software Engineer at Google Inc
    Worked on machine learning projects using Python and TensorFlow
    Professional experience in cloud computing and database management
    """

    work_keywords = extract_work_experience_keywords(sample_cv)
    enhanced_query = f"{base_query} {work_keywords}".strip()

    print(f"🔍 工作关键词: '{work_keywords}'")
    print(f"🎯 Enhanced query: '{enhanced_query}'")

    print(f"\n📊 Query comparison:")
    print(f"- Original length: {len(base_query.split())} 词")
    print(f"- Enhanced length: {len(enhanced_query.split())} 词")
    print(
        f"- Enhancement ratio: {len(enhanced_query.split())/len(base_query.split()):.1f}x")


if __name__ == "__main__":
    print("🧪 工作经历关键词提取Test")
    print("=" * 50)

    # Test1: 关键词提取
    keywords = test_work_keywords_extraction()

    # Test2: 查询增强
    test_query_enhancement()

    print("\n✅ Test completed！")
