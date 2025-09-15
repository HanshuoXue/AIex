"use client";

import { useState } from "react";
import type { Candidate } from "../../types";

// 统一的 API 配置
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api-alex-12345.azurewebsites.net'
  : 'http://127.0.0.1:8000';

interface CandidateFormProps {
  onMatch: (data: Candidate) => void;
  onDetailedMatch: (data: Candidate) => void;
  onAllMatch: (data: Candidate) => void;
  loading: boolean;
}

export default function CandidateForm({
  onMatch,
  onDetailedMatch,
  onAllMatch,
  loading,
}: CandidateFormProps) {
  const [formData, setFormData] = useState({
    bachelor_major: "computer science",
    gpa_scale: "4.0",
    gpa_value: 3.5,
    ielts_overall: 7.0,
    ielts_subscores: {
      listening: 7.0,
      reading: 7.0,
      writing: 6.5,
      speaking: 7.0,
    },
    work_years: 1,
    interests: ["artificial intelligence", "machine learning"],
    city_pref: ["Wellington", "Auckland"],
    budget_nzd_per_year: 60000,
  });

  const [cvFile, setCvFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [cvExtractedText, setCvExtractedText] = useState<string | null>(null);
  const [cvUploadStatus, setCvUploadStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'success' | 'error'>('idle');
  const [cvAiAnalysis, setCvAiAnalysis] = useState<Candidate['cv_analysis'] | null>(null);
  const [qaAnswers, setQaAnswers] = useState<{[key: string]: string}>({});
  const [currentQaIndex, setCurrentQaIndex] = useState<number>(0);
  const [showQa, setShowQa] = useState<boolean>(false);
  const [qaQuestions, setQaQuestions] = useState<Array<{
    id: string;
    question: string;
    placeholder: string;
    required: boolean;
    reason: string;
  }>>([]);
  const [qaAnalysis, setQaAnalysis] = useState<{
    questions: Array<{
      id: string;
      question: string;
      placeholder: string;
      required: boolean;
      reason: string;
    }>;
    analysis_summary: string;
    priority_areas: string[];
  } | null>(null);

  const handleChange = (
    field: keyof Candidate,
    value: string | number | string[]
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayChange = (field: string, value: string) => {
    const items = value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item);
    setFormData((prev) => ({
      ...prev,
      [field]: items,
    }));
  };

  const handleIeltsChange = (skill: string, value: number) => {
    setFormData((prev) => ({
      ...prev,
      ielts_subscores: {
        ...prev.ielts_subscores,
        [skill]: value,
      },
    }));
  };

  const handleFileChange = async (file: File) => {
    // 验证文件类型
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      alert('请上传 PDF 或 Word 文档格式的简历');
      return;
    }
    
    // 验证文件大小 (5MB 限制)
    if (file.size > 5 * 1024 * 1024) {
      alert('文件大小不能超过 5MB');
      return;
    }
    
    setCvFile(file);
    
    // 立即上传并处理 CV
    await uploadAndProcessCV(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const removeFile = () => {
    setCvFile(null);
    setCvExtractedText(null);
    setCvAiAnalysis(null);
    setQaAnswers({});
    setQaQuestions([]);
    setQaAnalysis(null);
    setCurrentQaIndex(0);
    setShowQa(false);
    setCvUploadStatus('idle');
  };

  const handleQaAnswer = (questionId: string, answer: string) => {
    setQaAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const nextQaQuestion = () => {
    if (currentQaIndex < qaQuestions.length - 1) {
      setCurrentQaIndex(prev => prev + 1);
    } else {
      setShowQa(false);
    }
  };

  const prevQaQuestion = () => {
    if (currentQaIndex > 0) {
      setCurrentQaIndex(prev => prev - 1);
    }
  };

  const startQa = () => {
    setShowQa(true);
    setCurrentQaIndex(0);
  };

  const uploadAndProcessCV = async (file: File) => {
    setCvUploadStatus('uploading');
    try {
      // 第一步：上传并提取文本
      const formDataWithFile = new FormData();
      formDataWithFile.append('cv', file);
      formDataWithFile.append('candidate_data', JSON.stringify(formData));
      
      const uploadResponse = await fetch(`${API_BASE_URL}/upload-cv`, {
        method: 'POST',
        body: formDataWithFile,
      });
      
      if (!uploadResponse.ok) {
        throw new Error('CV 上传失败');
      }
      
      const uploadResult = await uploadResponse.json();
      console.log('CV 上传成功:', uploadResult);
      
      if (uploadResult.success && uploadResult.upload_info?.extracted_cv_info) {
        // 立即显示提取的文本
        const extractedInfo = uploadResult.upload_info.extracted_cv_info;
        if (extractedInfo.extracted_text) {
          setCvExtractedText(extractedInfo.extracted_text);
          setCvUploadStatus('success');
          console.log('文本提取成功，长度:', extractedInfo.extracted_text.length);
        }
        
        // 第二步：进行AI分析
        setCvUploadStatus('analyzing');
        try {
          const analyzeFormData = new FormData();
          analyzeFormData.append('file_id', uploadResult.file_id);
          analyzeFormData.append('candidate_data', JSON.stringify(formData));
          
          const analyzeResponse = await fetch(`${API_BASE_URL}/analyze-cv`, {
            method: 'POST',
            body: analyzeFormData,
          });
          
          if (!analyzeResponse.ok) {
            throw new Error('AI 分析失败');
          }
          
          const analyzeResult = await analyzeResponse.json();
          console.log('AI 分析成功:', analyzeResult);
          console.log('generated_questions 原始数据:', analyzeResult.generated_questions);
          console.log('generated_questions 类型:', typeof analyzeResult.generated_questions);
          
          if (analyzeResult.success) {
            setCvUploadStatus('success');
            
            // 设置AI分析结果
            if (analyzeResult.ai_analysis) {
              let aiAnalysis = analyzeResult.ai_analysis;
              
              // 如果是字符串，需要解析为对象
              if (typeof aiAnalysis === 'string') {
                try {
                  // 清理 markdown 代码块标记
                  let cleanedData = aiAnalysis;
                  // 移除 ```json 和 ``` 标记
                  cleanedData = cleanedData.replace(/```json\s*/g, '').replace(/```\s*/g, '');
                  // 移除其他可能的标记
                  cleanedData = cleanedData.trim();
                  
                  console.log('清理后的CV分析数据:', cleanedData);
                  aiAnalysis = JSON.parse(cleanedData);
                  console.log('解析后的CV分析数据:', aiAnalysis);
                } catch (e) {
                  console.error('解析CV分析数据失败:', e);
                  console.error('原始CV分析数据:', analyzeResult.ai_analysis);
                  // 如果解析失败，使用原始数据
                  aiAnalysis = analyzeResult.ai_analysis;
                }
              }
              
              setCvAiAnalysis(aiAnalysis);
              console.log('AI 分析结果:', aiAnalysis);
            }
            
            // 处理生成的问题
            if (analyzeResult.generated_questions) {
              let questionsData = analyzeResult.generated_questions;
              
              // 如果是字符串，需要解析为对象
              if (typeof questionsData === 'string') {
                try {
                  // 清理 markdown 代码块标记
                  let cleanedData = questionsData;
                  // 移除 ```json 和 ``` 标记
                  cleanedData = cleanedData.replace(/```json\s*/g, '').replace(/```\s*/g, '');
                  // 移除其他可能的标记
                  cleanedData = cleanedData.trim();
                  
                  console.log('清理后的数据:', cleanedData);
                  questionsData = JSON.parse(cleanedData);
                  console.log('解析后的问题数据:', questionsData);
                } catch (e) {
                  console.error('解析问题数据失败:', e);
                  console.error('原始数据:', analyzeResult.generated_questions);
                  return;
                }
              }
              
              console.log('生成的问题数据:', questionsData);
              console.log('问题数组:', questionsData.questions);
              console.log('问题数组类型:', typeof questionsData.questions);
              console.log('问题数组长度:', questionsData.questions?.length);
              
              setQaQuestions(questionsData.questions || []);
              setQaAnalysis(questionsData);
              
              console.log('设置后的 qaQuestions 长度应该是:', questionsData.questions?.length);
              
              // 如果有问题，自动开始 Q&A
              if (questionsData.questions && questionsData.questions.length > 0) {
                console.log('发现问题，准备开始 Q&A');
                console.log('问题详情:', questionsData.questions);
                setTimeout(() => {
                  console.log('设置 showQa 为 true');
                  setShowQa(true);
                  setCurrentQaIndex(0);
                }, 500);
              }
            }
          }
        } catch (analyzeError) {
          console.error('AI 分析错误:', analyzeError);
          setCvUploadStatus('success'); // 文本提取成功了，只是AI分析失败
        }
      } else {
        setCvUploadStatus('error');
        console.error('CV 处理失败:', uploadResult.error);
      }
      
    } catch (error) {
      console.error('CV 上传错误:', error);
      setCvUploadStatus('error');
    }
  };

  const handleSubmit = async (e: React.FormEvent, isDetailed = false) => {
    e.preventDefault();
    
    // 将 Q&A 答案添加到表单数据中，确保不为 undefined
    const enhancedFormData: Candidate = {
      ...formData
    };
    
    // Only add qa_answers if it exists and has content
    if (qaAnswers && Object.keys(qaAnswers).length > 0) {
      enhancedFormData.qa_answers = qaAnswers;
    }
    
    // Only add cv_analysis if it exists
    if (cvAiAnalysis) {
      enhancedFormData.cv_analysis = cvAiAnalysis;
    }
    
    console.log('发送的数据:', enhancedFormData);
    console.log('qa_answers:', enhancedFormData.qa_answers);
    console.log('cv_analysis:', enhancedFormData.cv_analysis);
    
    // CV 已经在文件选择时处理了，直接进行匹配
    if (isDetailed) {
      onDetailedMatch(enhancedFormData);
    } else {
      onMatch(enhancedFormData);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm h-full flex flex-col">
      <div className="p-3 border-b border-gray-200 flex-shrink-0">
        <h2 className="text-lg font-bold text-gray-800">
          📋 Candidate Information
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <form className="space-y-3">
          {/* Academic background */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2 text-sm">
              🎓 Academic Background
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Bachelor&apos;s Major
                </label>
                <input
                  type="text"
                  value={formData.bachelor_major}
                  onChange={(e) =>
                    handleChange("bachelor_major", e.target.value)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="computer science"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  GPA ({formData.gpa_scale} scale)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="4"
                  value={formData.gpa_value}
                  onChange={(e) =>
                    handleChange("gpa_value", parseFloat(e.target.value))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* English proficiency */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2 text-sm">
              🗣️ English Proficiency
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  IELTS Overall
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="9"
                  value={formData.ielts_overall}
                  onChange={(e) =>
                    handleChange("ielts_overall", parseFloat(e.target.value))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {Object.entries(formData.ielts_subscores).map(
                ([skill, score]) => (
                  <div key={skill}>
                    <label className="block text-sm font-medium text-gray-600 mb-1">
                      {skill === "listening"
                        ? "Listening"
                        : skill === "reading"
                        ? "Reading"
                        : skill === "writing"
                        ? "Writing"
                        : "Speaking"}
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      max="9"
                      value={score}
                      onChange={(e) =>
                        handleIeltsChange(skill, parseFloat(e.target.value))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                )
              )}
            </div>
          </div>

          {/* Personal preferences */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2 text-sm">
              💡 Personal Preferences
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Work Experience (years)
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.work_years}
                  onChange={(e) =>
                    handleChange("work_years", parseInt(e.target.value))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Interest Areas (comma separated)
                </label>
                <input
                  type="text"
                  value={formData.interests.join(", ")}
                  onChange={(e) =>
                    handleArrayChange("interests", e.target.value)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="artificial intelligence, machine learning"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  City Preferences (comma separated)
                </label>
                <input
                  type="text"
                  value={formData.city_pref.join(", ")}
                  onChange={(e) =>
                    handleArrayChange("city_pref", e.target.value)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Wellington, Auckland"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Annual Budget (NZD)
                </label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={formData.budget_nzd_per_year}
                  onChange={(e) =>
                    handleChange(
                      "budget_nzd_per_year",
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* CV Upload Section */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-3">
              📄 CV Upload (Optional)
            </h3>
            
            {!cvFile ? (
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  isDragOver
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="space-y-2">
                  <div className="text-4xl">📄</div>
                  <p className="text-sm text-gray-600">
                    拖拽 CV 文件到这里，或点击选择文件
                  </p>
                  <p className="text-xs text-gray-500">
                    支持 PDF, DOC, DOCX 格式，最大 5MB
                  </p>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileInputChange}
                    className="hidden"
                    id="cv-upload"
                  />
                  <label
                    htmlFor="cv-upload"
                    className="inline-block px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 cursor-pointer transition-colors"
                  >
                    选择文件
                  </label>
                </div>
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">📄</div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {cvFile.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    移除
                  </button>
                </div>
                
                {/* 上传状态 */}
                {cvUploadStatus === 'uploading' && (
                  <div className="flex items-center space-x-2 text-blue-600 text-sm">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span>正在上传 CV...</span>
                  </div>
                )}
                
                {cvUploadStatus === 'analyzing' && (
                  <div className="flex items-center space-x-2 text-orange-600 text-sm">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                    <span>正在AI分析中...</span>
                  </div>
                )}
                
                {cvUploadStatus === 'success' && (
                  <div className="flex items-center space-x-2 text-green-600 text-sm mb-3">
                    <span>✅</span>
                    <span>CV 处理成功</span>
                  </div>
                )}
                
                {cvUploadStatus === 'error' && (
                  <div className="flex items-center space-x-2 text-red-600 text-sm mb-3">
                    <span>❌</span>
                    <span>CV 处理失败</span>
                  </div>
                )}
                
                {/* 提取的文本预览 */}
                {cvExtractedText && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      📝 提取的文本内容 (前200字符):
                    </h4>
                    <div className="bg-gray-50 p-3 rounded text-xs text-gray-600 max-h-32 overflow-y-auto">
                      {cvExtractedText.substring(0, 200)}
                      {cvExtractedText.length > 200 && '...'}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      总长度: {cvExtractedText.length} 字符
                    </p>
                  </div>
                )}
                
                {/* AI 分析结果 */}
                {cvAiAnalysis && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">
                        🤖 AI 分析结果:
                      </h4>
                      <button
                        type="button"
                        onClick={() => {
                          console.log('完整AI分析结果:', cvAiAnalysis);
                          console.log('AI分析结果JSON:', JSON.stringify(cvAiAnalysis, null, 2));
                        }}
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                      >
                        打印到控制台
                      </button>
                    </div>
                    <div className="bg-blue-50 p-3 rounded text-xs text-gray-700 max-h-80 overflow-y-auto">
                      {cvAiAnalysis.personal_info && (
                        <div className="mb-2">
                          <strong>个人信息:</strong>
                          <div className="ml-2 text-xs">
                            {cvAiAnalysis.personal_info.name && <div>姓名: {cvAiAnalysis.personal_info.name}</div>}
                            {cvAiAnalysis.personal_info.email && <div>邮箱: {cvAiAnalysis.personal_info.email}</div>}
                            {cvAiAnalysis.personal_info.phone && <div>电话: {cvAiAnalysis.personal_info.phone}</div>}
                          </div>
                        </div>
                      )}
                      
                      {cvAiAnalysis.work_experience && cvAiAnalysis.work_experience.length > 0 && (
                        <div className="mb-2">
                          <strong>工作经历:</strong>
                          <div className="ml-2 text-xs">
                            {cvAiAnalysis.work_experience.map((exp, index: number) => (
                              <div key={index} className="mt-1">
                                {exp.company} - {exp.position} ({exp.start_date} - {exp.end_date})
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {cvAiAnalysis.skills && (
                        <div className="mb-2">
                          <strong>技能:</strong>
                          <div className="ml-2 text-xs">
                            {cvAiAnalysis.skills.programming_languages && (
                              <div>编程语言: {cvAiAnalysis.skills.programming_languages.join(', ')}</div>
                            )}
                            {cvAiAnalysis.skills.tools_and_frameworks && (
                              <div>工具框架: {cvAiAnalysis.skills.tools_and_frameworks.join(', ')}</div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {cvAiAnalysis.gaps_identified && cvAiAnalysis.gaps_identified.length > 0 && (
                        <div className="mb-2">
                          <strong>⚠️ 发现的空白期:</strong>
                          <div className="ml-2 text-xs">
                            {cvAiAnalysis.gaps_identified.map((gap, index: number) => (
                              <div key={index} className="text-orange-600">
                                {gap.start_date} - {gap.end_date} ({gap.duration_months}个月): {gap.reason_inferred}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Q&A 对话组件 */}
          {cvUploadStatus === 'success' && qaQuestions.length > 0 && !showQa && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 mb-3">
                💬 个性化问题
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                基于您的简历分析，我们为您准备了 {qaQuestions.length} 个个性化问题，这将帮助我们更准确地为您匹配合适的课程：
              </p>
              {qaAnalysis && qaAnalysis.analysis_summary && (
                <div className="bg-blue-100 p-3 rounded mb-3">
                  <p className="text-xs text-blue-800">
                    <strong>分析摘要：</strong>{qaAnalysis.analysis_summary}
                  </p>
                </div>
              )}
              <button
                type="button"
                onClick={startQa}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
              >
                开始个性化问答
              </button>
            </div>
          )}

          {showQa && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700">
                  💬 补充信息 ({currentQaIndex + 1}/{qaQuestions.length})
                </h3>
                <button
                  type="button"
                  onClick={() => setShowQa(false)}
                  className="text-gray-500 hover:text-gray-700 text-sm"
                >
                  ✕ 跳过
                </button>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-800 mb-2">
                  {qaQuestions[currentQaIndex].question}
                </h4>
                {qaQuestions[currentQaIndex].reason && (
                  <p className="text-xs text-blue-600 mb-2">
                    💡 {qaQuestions[currentQaIndex].reason}
                  </p>
                )}
                <textarea
                  value={qaAnswers[qaQuestions[currentQaIndex].id] || ''}
                  onChange={(e) => handleQaAnswer(qaQuestions[currentQaIndex].id, e.target.value)}
                  placeholder={qaQuestions[currentQaIndex].placeholder}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={4}
                />
                {qaQuestions[currentQaIndex].required && (
                  <p className="text-xs text-red-500 mt-1">* 此问题为必填项</p>
                )}
              </div>

              <div className="flex justify-between">
                <button
                  type="button"
                  onClick={prevQaQuestion}
                  disabled={currentQaIndex === 0}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  上一题
                </button>
                
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowQa(false)}
                    className="px-4 py-2 bg-gray-500 text-white text-sm rounded-md hover:bg-gray-600 transition-colors"
                  >
                    跳过
                  </button>
                  
                  <button
                    type="button"
                    onClick={nextQaQuestion}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {currentQaIndex === qaQuestions.length - 1 ? '完成' : '下一题'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Quick template buttons */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2 text-sm">
              ⚡ Quick Test Templates
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => {
                  setFormData({
                    bachelor_major: "computer science",
                    gpa_scale: "4.0",
                    gpa_value: 3.7,
                    ielts_overall: 7.5,
                    ielts_subscores: {
                      listening: 8.0,
                      reading: 7.5,
                      writing: 7.0,
                      speaking: 7.5,
                    },
                    work_years: 2,
                    interests: [
                      "artificial intelligence",
                      "machine learning",
                      "data science",
                    ],
                    city_pref: ["Wellington"],
                    budget_nzd_per_year: 70000,
                  });
                }}
                className="bg-green-100 text-green-800 py-2 px-4 rounded-lg font-medium hover:bg-green-200 transition-colors duration-200 text-sm"
              >
                💻 Computer Science Template
                <div className="text-xs mt-1 opacity-75">
                  High GPA • High IELTS • AI Interest • Sufficient Budget
                </div>
              </button>

              <button
                type="button"
                onClick={() => {
                  setFormData({
                    bachelor_major: "business administration",
                    gpa_scale: "4.0",
                    gpa_value: 3.2,
                    ielts_overall: 6.5,
                    ielts_subscores: {
                      listening: 6.5,
                      reading: 7.0,
                      writing: 6.0,
                      speaking: 6.5,
                    },
                    work_years: 0,
                    interests: ["business management", "marketing"],
                    city_pref: ["Auckland"],
                    budget_nzd_per_year: 45000,
                  });
                }}
                className="bg-blue-100 text-blue-800 py-2 px-4 rounded-lg font-medium hover:bg-blue-200 transition-colors duration-200 text-sm"
              >
                📊 Business Management Template
                <div className="text-xs mt-1 opacity-75">
                  Medium GPA • Standard IELTS • Business Background • Limited
                  Budget
                </div>
              </button>
            </div>
          </div>

          {/* Submit buttons */}
          <div className="space-y-3 pt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={(e) => handleSubmit(e, false)}
                disabled={loading}
                className="bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {loading ? "Matching..." : "🚀 Quick Match"}
              </button>

              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                disabled={loading}
                className="bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {loading ? "Analyzing..." : "📊 Detailed Analysis"}
              </button>
            </div>

            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                
                // 使用相同的增强数据逻辑
                const enhancedFormData: Candidate = {
                  ...formData
                };
                
                // Only add qa_answers if it exists and has content
                if (qaAnswers && Object.keys(qaAnswers).length > 0) {
                  enhancedFormData.qa_answers = qaAnswers;
                }
                
                // Only add cv_analysis if it exists
                if (cvAiAnalysis) {
                  enhancedFormData.cv_analysis = cvAiAnalysis;
                }
                
                console.log('Complete Analysis 发送的数据:', enhancedFormData);
                onAllMatch(enhancedFormData);
              }}
              disabled={loading}
              className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {loading
                ? "Full analysis..."
                : "🔍 Complete Analysis (including rejected programs)"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
