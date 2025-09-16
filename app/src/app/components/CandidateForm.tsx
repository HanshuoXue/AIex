"use client";

import { useState } from "react";
import type { Candidate } from "../../types";

// Unified API configuration
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
  const [analysisMetadata, setAnalysisMetadata] = useState<{
    analysis_method?: string;
    flow_used?: string;
    chunking_method?: string;
    text_length?: number;
    query_info?: {
      base_query: string;
      work_keywords_extracted: string;
      final_query: string;
      query_enhancement_ratio: number;
    };
    chunk_info?: {
      total_chunks: number;
      relevant_chunks_used: number;
      avg_chunk_tokens: number;
      chunking_successful: boolean;
    };
    chunk_details?: {
      all_chunks_summary: Array<{
        id: string;
        text_preview: string;
        length: number;
        estimated_tokens: number;
      }>;
      relevant_chunks: Array<{
        id: string;
        text_preview: string;
        full_text: string;
        length: number;
        estimated_tokens: number;
        relevance_score: number;
        rank: number;
      }>;
    };
  } | null>(null);
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
  const [showChunkDetails, setShowChunkDetails] = useState<boolean>(false);

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
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a resume in PDF or Word document format');
      return;
    }
    
    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size cannot exceed 5MB');
      return;
    }
    
    setCvFile(file);
    
    // Immediately upload and process CV
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
    setAnalysisMetadata(null);
    setQaAnswers({});
    setQaQuestions([]);
    setQaAnalysis(null);
    setCurrentQaIndex(0);
    setShowQa(false);
    setShowChunkDetails(false);
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
      // Step 1: Upload and extract text
      const formDataWithFile = new FormData();
      formDataWithFile.append('cv', file);
      formDataWithFile.append('candidate_data', JSON.stringify(formData));
      
      const uploadResponse = await fetch(`${API_BASE_URL}/upload-cv`, {
        method: 'POST',
        body: formDataWithFile,
      });
      
      if (!uploadResponse.ok) {
        throw new Error('CV upload failed');
      }
      
      const uploadResult = await uploadResponse.json();
      console.log('CV uploaded successfully:', uploadResult);
      
      if (uploadResult.success && uploadResult.upload_info?.extracted_cv_info) {
        // Immediately display extracted text
        const extractedInfo = uploadResult.upload_info.extracted_cv_info;
        if (extractedInfo.extracted_text) {
          setCvExtractedText(extractedInfo.extracted_text);
          setCvUploadStatus('success');
          console.log('Text extraction successful, length:', extractedInfo.extracted_text.length);
        }
        
        // Step 2: Perform AI analysis
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
            throw new Error('AI analysis failed');
          }
          
          const analyzeResult = await analyzeResponse.json();
          console.log('AI analysis successful:', analyzeResult);
            console.log('generated_questions raw data:', analyzeResult.generated_questions);
            console.log('generated_questions type:', typeof analyzeResult.generated_questions);
          
          if (analyzeResult.success) {
            setCvUploadStatus('success');
            
            // Set analysis metadata
            if (analyzeResult.analysis_metadata) {
              setAnalysisMetadata(analyzeResult.analysis_metadata);
              console.log('Analysis metadata:', analyzeResult.analysis_metadata);
            }
            
            // Set AI analysis results
            if (analyzeResult.ai_analysis) {
              let aiAnalysis = analyzeResult.ai_analysis;
              
              // If it's a string, need to parse as object
              if (typeof aiAnalysis === 'string') {
                try {
                  // Clean markdown code block markers
                  let cleanedData = aiAnalysis;
                  // Remove ```json and ``` markers
                  cleanedData = cleanedData.replace(/```json\s*/g, '').replace(/```\s*/g, '');
                  // Remove other possible markers
                  cleanedData = cleanedData.trim();
                  
                  console.log('Cleaned CV analysis data:', cleanedData);
                  aiAnalysis = JSON.parse(cleanedData);
                  console.log('Parsed CV analysis data:', aiAnalysis);
                } catch (e) {
                  console.error('Failed to parse CV analysis data:', e);
                  console.error('Original CV analysis data:', analyzeResult.ai_analysis);
                  // If parsing fails, use original data
                  aiAnalysis = analyzeResult.ai_analysis;
                }
              }
              
              setCvAiAnalysis(aiAnalysis);
              console.log('AI Analysis Results:', aiAnalysis);
            }
            
            // Process generated questions
            if (analyzeResult.generated_questions) {
              let questionsData = analyzeResult.generated_questions;
              
              // If it's a string, need to parse as object
              if (typeof questionsData === 'string') {
                try {
                  // Clean markdown code block markers
                  let cleanedData = questionsData;
                  // Remove ```json and ``` markers
                  cleanedData = cleanedData.replace(/```json\s*/g, '').replace(/```\s*/g, '');
                  // Remove other possible markers
                  cleanedData = cleanedData.trim();
                  
                  console.log('Cleaned data:', cleanedData);
                  questionsData = JSON.parse(cleanedData);
                  console.log('Parsed question data:', questionsData);
                } catch (e) {
                  console.error('Failed to parse question data:', e);
                  console.error('Original data:', analyzeResult.generated_questions);
                  return;
                }
              }
              
              console.log('Generated question data:', questionsData);
              console.log('Question array:', questionsData.questions);
              console.log('Question array type:', typeof questionsData.questions);
              console.log('Question array length:', questionsData.questions?.length);
              
              setQaQuestions(questionsData.questions || []);
              setQaAnalysis(questionsData);
              
              console.log('After setting, qaQuestions length should be:', questionsData.questions?.length);
              
              // If there are questions, automatically start Q&A
              if (questionsData.questions && questionsData.questions.length > 0) {
                console.log('Found questions, preparing to start Q&A');
                console.log('Question details:', questionsData.questions);
                setTimeout(() => {
                  console.log('Set showQa to true');
                  setShowQa(true);
                  setCurrentQaIndex(0);
                }, 500);
              }
            }
          }
        } catch (analyzeError) {
          console.error('AI analysis error:', analyzeError);
          setCvUploadStatus('success'); // Text extraction succeeded, only AI analysis failed
        }
      } else {
        setCvUploadStatus('error');
        console.error('CV processing failed:', uploadResult.error);
      }
      
    } catch (error) {
      console.error('CV upload error:', error);
      setCvUploadStatus('error');
    }
  };

  const handleSubmit = async (e: React.FormEvent, isDetailed = false) => {
    e.preventDefault();
    
    // Add Q&A answers to form data, ensure not undefined
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
    
    console.log('Data being sent:', enhancedFormData);
    console.log('qa_answers:', enhancedFormData.qa_answers);
    console.log('cv_analysis:', enhancedFormData.cv_analysis);
    
    // CV has been processed during file selection, proceed directly to matching
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
                    Drag CV file here, or click to select file
                  </p>
                  <p className="text-xs text-gray-500">
                    Supports PDF, DOC, DOCX formats, maximum 5MB
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
                    Select File
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
                    Remove
                  </button>
                </div>
                
                {/* Upload Status */}
                {cvUploadStatus === 'uploading' && (
                  <div className="flex items-center space-x-2 text-blue-600 text-sm">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span>Uploading CV...</span>
                  </div>
                )}
                
                {cvUploadStatus === 'analyzing' && (
                  <div className="flex items-center space-x-2 text-orange-600 text-sm">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                    <span>AI analyzing...</span>
                  </div>
                )}
                
                {cvUploadStatus === 'success' && (
                  <div className="flex items-center space-x-2 text-green-600 text-sm mb-3">
                    <span>✅</span>
                    <span>CV processing successful</span>
                  </div>
                )}
                
                {cvUploadStatus === 'error' && (
                  <div className="flex items-center space-x-2 text-red-600 text-sm mb-3">
                    <span>❌</span>
                    <span>CV processing failed</span>
                  </div>
                )}
                
                {/* Extracted Text Preview */}
                {cvExtractedText && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      📝 Extracted text content (first 200 characters):
                    </h4>
                    <div className="bg-gray-50 p-3 rounded text-xs text-gray-600 max-h-32 overflow-y-auto">
                      {cvExtractedText.substring(0, 200)}
                      {cvExtractedText.length > 200 && '...'}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Total length: {cvExtractedText.length} characters
                    </p>
                  </div>
                )}
                
                {/* Analysis Method Information */}
                {analysisMetadata && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      ⚙️ Analysis Method Information:
                    </h4>
                    <div className="bg-indigo-50 p-3 rounded text-xs">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="font-medium">Analysis Method:</span>
                          <span className={`ml-1 px-2 py-1 rounded text-xs ${
                            analysisMetadata.analysis_method === 'RAG-based' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {analysisMetadata.analysis_method}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Flow File:</span>
                          <span className="ml-1 text-gray-600">{analysisMetadata.flow_used}</span>
                        </div>
                        <div>
                          <span className="font-medium">Text Length:</span>
                          <span className="ml-1 text-gray-600">{analysisMetadata.text_length} characters</span>
                        </div>
                        {analysisMetadata.chunking_method && (
                          <div>
                            <span className="font-medium">Chunking Method:</span>
                            <span className="ml-1 text-gray-600">{analysisMetadata.chunking_method}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Chunk Information */}
                      {analysisMetadata.chunk_info && (
                        <div className="mt-2 pt-2 border-t border-indigo-200">
                          <div className="font-medium mb-1">📊 Chunk Statistics:</div>
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <span className="font-medium">Total Chunks:</span>
                              <span className="ml-1 text-green-700">{analysisMetadata.chunk_info.total_chunks}</span>
                            </div>
                            <div>
                              <span className="font-medium">Relevant Chunks:</span>
                              <span className="ml-1 text-green-700">{analysisMetadata.chunk_info.relevant_chunks_used}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Query Enhancement Information */}
                      {analysisMetadata.query_info && (
                        <div className="mt-2 pt-2 border-t border-orange-200">
                          <div className="font-medium mb-1">🔍 Query Enhancement Information:</div>
                          
                          {/* Work Keywords */}
                          <div className="mb-2">
                            <div className="font-medium text-sm text-orange-700 mb-1">Work Keywords Extracted from CV:</div>
                            <div className="bg-orange-50 p-2 rounded border">
                              {analysisMetadata.query_info.work_keywords_extracted ? (
                                <div className="flex flex-wrap gap-1">
                                  {analysisMetadata.query_info.work_keywords_extracted.split(' ').map((keyword: string, index: number) => (
                                    <span key={index} className="inline-block bg-orange-200 text-orange-800 text-xs px-2 py-1 rounded">
                                      {keyword}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-gray-500 text-sm">No work keywords extracted</span>
                              )}
                            </div>
                          </div>

                          {/* Query Comparison */}
                          <div className="grid grid-cols-1 gap-2">
                            <div>
                              <span className="font-medium text-sm">Original Query:</span>
                              <div className="text-xs text-gray-600 bg-gray-50 p-1 rounded mt-1">
                                &ldquo;{analysisMetadata.query_info.base_query}&rdquo;
                              </div>
                            </div>
                            <div>
                              <span className="font-medium text-sm">Enhanced Query:</span>
                              <div className="text-xs text-gray-600 bg-blue-50 p-1 rounded mt-1">
                                &ldquo;{analysisMetadata.query_info.final_query}&rdquo;
                              </div>
                            </div>
                            <div>
                              <span className="font-medium text-sm">Enhancement Ratio:</span>
                              <span className="ml-1 text-blue-700 font-bold">
                                {analysisMetadata.query_info.query_enhancement_ratio?.toFixed(1)}x
                              </span>
                            </div>
                          </div>
                          
                          {/* Simplified RAG Information */}
                          {analysisMetadata.chunk_info?.avg_chunk_tokens && (
                            <div className="mt-2">
                              <div className="text-xs text-gray-600">
                                <span className="font-medium">Average Chunk Size:</span>
                                <span className="ml-1">{analysisMetadata.chunk_info.avg_chunk_tokens} tokens</span>
                                <span className="ml-2 text-green-600">✓ Fixed Token Chunking</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Chunk Details Button */}
                      {analysisMetadata.chunk_details && (
                        <div className="mt-3">
                          <button
                            type="button"
                            onClick={() => setShowChunkDetails(!showChunkDetails)}
                            className="text-sm bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700 transition-colors"
                          >
                            {showChunkDetails ? '🔼 Hide Chunk Details' : '🔽 View Chunk Details'}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Chunk Details Display */}
                {showChunkDetails && analysisMetadata?.chunk_details && (
                  <div className="mt-3">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">
                        📊 Chunk Analysis Details
                      </h4>
                      
                      {/* Complete Chunk Content Sent to LLM */}
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-purple-700 mb-2">
                          🚀 Complete Chunk Content Sent to LLM (for generating personalized questions)
                        </h5>
                        <div className="bg-purple-50 border border-purple-200 p-3 rounded">
                          <div className="text-xs text-purple-600 mb-2">
                            📝 Following are the actual chunks sent to GPT-4{analysisMetadata.chunk_details.relevant_chunks?.length || 0} complete content of the most relevant chunks
                          </div>
                          <div className="space-y-3 max-h-96 overflow-y-auto">
                            {analysisMetadata.chunk_details.relevant_chunks?.map((chunk) => (
                              <div key={chunk.id} className="bg-white border border-purple-300 rounded-lg">
                                {/* Chunk Header Information */}
                                <div className="bg-purple-100 px-3 py-2 rounded-t-lg border-b border-purple-200">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-2">
                                      <span className="inline-block bg-purple-600 text-white text-xs px-2 py-1 rounded font-bold">
                                        Rank #{chunk.rank}
                                      </span>
                                      <span className="text-xs font-mono text-purple-600">{chunk.id}</span>
                                      <span className="inline-block bg-red-500 text-white text-xs px-2 py-1 rounded">
                                        Relevance Score: {chunk.relevance_score}
                                      </span>
                                    </div>
                                    <div className="text-xs text-purple-600">
                                      {chunk.estimated_tokens} tokens • {chunk.length} characters
                                    </div>
                                  </div>
                                </div>
                                
                                {/* Complete Chunk Content */}
                                <div className="p-3">
                                  <div className="text-xs text-gray-800 leading-relaxed whitespace-pre-wrap font-mono">
                                    {chunk.full_text || chunk.text_preview}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          {/* Summary Information */}
                          <div className="mt-3 p-2 bg-purple-100 rounded text-xs text-purple-700">
                            💡 These chunks will be formatted and sent to LLM to generate personalized questions based on your CV and background
                          </div>
                        </div>
                      </div>

                      {/* Relevant Chunk Rankings (Simplified) */}
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-green-700 mb-2">
                          🎯 Chunk Ranking Overview (Top {analysisMetadata.chunk_details.relevant_chunks?.length || 0})
                        </h5>
                        <div className="space-y-2">
                          {analysisMetadata.chunk_details.relevant_chunks?.map((chunk) => (
                            <div key={chunk.id} className="bg-green-50 border border-green-200 p-3 rounded">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <span className="inline-block bg-green-600 text-white text-xs px-2 py-1 rounded font-bold">
                                    #{chunk.rank}
                                  </span>
                                  <span className="text-xs text-gray-600">{chunk.id}</span>
                                  <span className="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                                    Score: {chunk.relevance_score}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500">
                                  {chunk.estimated_tokens} tokens, {chunk.length} characters
                                </div>
                              </div>
                              <div className="text-xs text-gray-700 bg-white p-2 rounded border">
                                {chunk.text_preview}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* All Chunks Overview */}
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 mb-2">
                          📋 All Chunks Overview (first 10)
                        </h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {analysisMetadata.chunk_details.all_chunks_summary?.map((chunk) => (
                            <div key={chunk.id} className="bg-gray-100 border p-2 rounded text-xs">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-mono text-blue-600">{chunk.id}</span>
                                <span className="text-gray-500">{chunk.estimated_tokens}t</span>
                              </div>
                              <div className="text-gray-700 truncate">
                                {chunk.text_preview}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* AI Analysis Results */}
                {cvAiAnalysis && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">
                        🤖 AI Analysis Results:
                      </h4>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => {
                            console.log('Analysis metadata:', analysisMetadata);
                            console.log('Complete AI analysis results:', cvAiAnalysis);
                            console.log('AI analysis results JSON:', JSON.stringify(cvAiAnalysis, null, 2));
                          }}
                          className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                        >
                          Print complete information
                        </button>
                        {analysisMetadata?.analysis_method === 'RAG-based' && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                            RAG Enhanced Analysis
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="bg-blue-50 p-3 rounded text-xs text-gray-700">
                      <div className="mb-2">
                        <strong>✅ Analysis Type:</strong> Simple RAG
                      </div>
                      
                      <div className="mb-2">
                        <strong>📊 Analysis Chunks:</strong> {analysisMetadata?.chunk_info?.relevant_chunks_used || 0}
                      </div>
                      
                      <div className="mb-2">
                        <strong>🔍 Text Processing Status:</strong> 
                        <span className={analysisMetadata?.chunk_info?.chunking_successful ? 'text-green-600 ml-1' : 'text-red-600 ml-1'}>
                          {analysisMetadata?.chunk_info?.chunking_successful ? '✓ Processed' : '✗ Processing failed'}
                        </span>
                      </div>
                      
                      <div className="text-xs text-gray-500 mt-2">
                        💡 Simplified analysis completed - CV content has been converted to personalized questions
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Q&A Conversation Component */}
          {cvUploadStatus === 'success' && qaQuestions.length > 0 && !showQa && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 mb-3">
                💬 Personalized Questions
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Based on your resume analysis, we have prepared for you {qaQuestions.length} personalized questions, which will help us more accurately match suitable courses for you:
              </p>
              {qaAnalysis && qaAnalysis.analysis_summary && (
                <div className="bg-blue-100 p-3 rounded mb-3">
                  <p className="text-xs text-blue-800">
                    <strong>Analysis Summary：</strong>{qaAnalysis.analysis_summary}
                  </p>
                </div>
              )}
              <button
                type="button"
                onClick={startQa}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
              >
                Start Personalized Q&A
              </button>
            </div>
          )}

          {showQa && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700">
                  💬 Additional Information ({currentQaIndex + 1}/{qaQuestions.length})
                </h3>
                <button
                  type="button"
                  onClick={() => setShowQa(false)}
                  className="text-gray-500 hover:text-gray-700 text-sm"
                >
                  ✕ Skip
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
                  <p className="text-xs text-red-500 mt-1">* This question is required</p>
                )}
              </div>

              <div className="flex justify-between">
                <button
                  type="button"
                  onClick={prevQaQuestion}
                  disabled={currentQaIndex === 0}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous Question
                </button>
                
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowQa(false)}
                    className="px-4 py-2 bg-gray-500 text-white text-sm rounded-md hover:bg-gray-600 transition-colors"
                  >
                    Skip
                  </button>
                  
                  <button
                    type="button"
                    onClick={nextQaQuestion}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {currentQaIndex === qaQuestions.length - 1 ? 'Complete' : 'Next Question'}
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
                
                // Use the same enhanced data logic
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
                
                console.log('Complete Analysis Data being sent:', enhancedFormData);
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
