"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useAuth, apiCall } from '../../hooks/useAuth';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}

interface ConversationState {
  sessionId: string;
  cvUploaded: boolean;
  cvAnalysis?: any;
  sessionState: any;
  isComplete: boolean;
  isGeneratingReport: boolean;
}

const QA_QUESTIONS = [
  {
    id: 'cv_upload',
    question: '你好！我是您的新西兰留学助手。为了给您提供最精准的建议，请先上传您的简历(CV)，我将基于您的背景为您量身定制问题。',
    type: 'cv_upload',
    required: true
  },
  {
    id: 'study_motivation',
    question: '基于您的简历，我想了解您选择来新西兰留学的主要动机是什么？是为了职业发展、学术研究还是个人兴趣？',
    type: 'text',
    required: true
  },
  {
    id: 'preferred_field',
    question: '您希望在新西兰学习哪个专业领域？这与您当前的背景有什么联系？',
    type: 'text',
    required: true
  },
  {
    id: 'career_goals',
    question: '完成学业后，您的职业规划是什么？希望在哪个行业或领域发展？',
    type: 'text',
    required: true
  },
  {
    id: 'study_level',
    question: '您倾向于申请本科还是研究生课程？为什么？',
    type: 'choice',
    choices: ['本科课程', '研究生课程', '都可以考虑'],
    required: true
  },
  {
    id: 'location_preference',
    question: '您对新西兰的哪个城市更感兴趣？奥克兰、惠灵顿、基督城还是其他？',
    type: 'text',
    required: true
  },
  {
    id: 'budget_range',
    question: '您的年度学费预算大概是多少新西兰元？这将帮助我为您推荐合适的课程。',
    type: 'text',
    required: true
  },
  {
    id: 'english_proficiency',
    question: '您的英语水平如何？是否已经参加过雅思或托福考试？',
    type: 'text',
    required: true
  },
  {
    id: 'work_experience',
    question: '您有相关的工作经验吗？这些经验如何与您的学习目标相关联？',
    type: 'text',
    required: true
  },
  {
    id: 'special_requirements',
    question: '您是否有任何特殊要求或关注点？比如课程时长、实习机会、研究项目等？',
    type: 'text',
    required: false
  }
];

export default function QAAssistant() {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationState, setConversationState] = useState<ConversationState>({
    sessionId: Date.now().toString(),
    cvUploaded: false,
    sessionState: {},
    isComplete: false,
    isGeneratingReport: false
  });
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 初始化对话
  useEffect(() => {
    const initializeConversation = async () => {
      try {
        const response = await apiCall('/api/qa-assistant/conversation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            conversation_history: { messages: [] },
            user_message: "你好，我想了解新西兰留学",
            cv_analysis: {},
            session_state: conversationState.sessionState
          })
        });

        if (response.success && response.response) {
          const welcomeMessage: Message = {
            id: 'welcome',
            type: 'assistant',
            content: response.response.content || '你好！我是您的新西兰留学助手。请告诉我您的留学需求，或者上传您的简历让我更好地了解您的背景。',
            timestamp: new Date()
          };
          setMessages([welcomeMessage]);
          
          // 更新会话状态
          if (response.session_update) {
            setConversationState(prev => ({
              ...prev,
              sessionState: response.session_update.updated_session_state
            }));
          }
        } else {
          // Fallback 欢迎消息
          const fallbackMessage: Message = {
            id: 'welcome',
            type: 'assistant',
            content: '你好！我是您的新西兰留学助手。为了给您提供最精准的建议，请先上传您的简历(CV)，我将基于您的背景为您量身定制问题。',
            timestamp: new Date()
          };
          setMessages([fallbackMessage]);
        }
      } catch (error) {
        console.error('Failed to initialize conversation:', error);
        // Fallback 欢迎消息
        const fallbackMessage: Message = {
          id: 'welcome',
          type: 'assistant',
          content: '你好！我是您的新西兰留学助手。请告诉我您对新西兰留学最关心的问题是什么？',
          timestamp: new Date()
        };
        setMessages([fallbackMessage]);
      }
    };

    initializeConversation();
  }, []);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 添加消息
  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  // 添加打字效果消息
  const addTypingMessage = async (content: string) => {
    const typingMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isTyping: true
    };
    
    setMessages(prev => [...prev, typingMessage]);
    
    // 模拟打字效果
    for (let i = 0; i <= content.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 30));
      setMessages(prev => 
        prev.map(msg => 
          msg.id === typingMessage.id 
            ? { ...msg, content: content.slice(0, i), isTyping: i < content.length }
            : msg
        )
      );
    }
  };

  // 处理CV上传
  const handleCVUpload = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('cv', selectedFile);
      formData.append('candidate_data', JSON.stringify({
        bachelor_major: '',
        interests: [],
        city_pref: []
      }));

      const uploadResponse = await apiCall('/upload-cv', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (uploadResponse.success) {
        // 分析CV
        const analyzeFormData = new FormData();
        analyzeFormData.append('file_id', uploadResponse.file_id);
        analyzeFormData.append('candidate_data', JSON.stringify({
          bachelor_major: '',
          interests: [],
          city_pref: []
        }));

        const analysisResponse = await apiCall('/analyze-cv', {
          method: 'POST',
          body: analyzeFormData,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('CV分析响应:', analysisResponse);

        // 检查分析是否成功
        if (analysisResponse.success && analysisResponse.ai_analysis) {
          // 更新状态
          setConversationState(prev => ({
            ...prev,
            cvUploaded: true,
            cvAnalysis: analysisResponse.ai_analysis,
            sessionState: {
              ...prev.sessionState,
              cv_uploaded: true,
              cv_analysis_completed: true
            }
          }));

          // 添加成功消息
          addMessage({
            type: 'user',
            content: `已上传简历: ${selectedFile.name}`
          });

        // 调用智能对话API处理CV上传后的响应
        try {
          // 添加CV上传消息到历史中
          const updatedMessages = [...messages, {
            id: Date.now().toString(),
            type: 'user' as const,
            content: `已上传简历: ${selectedFile.name}`,
            timestamp: new Date()
          }];
          
          const conversationHistory = {
            messages: updatedMessages.map(msg => ({
              type: msg.type,
              content: msg.content,
              timestamp: msg.timestamp.toISOString()
            }))
          };

          const response = await apiCall('/api/qa-assistant/conversation', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              conversation_history: conversationHistory,
              user_message: `cv_uploaded:${selectedFile.name}`,
              cv_analysis: analysisResponse.ai_analysis,
              session_state: conversationState.sessionState
            })
          });

          if (response.success && response.response) {
            await addTypingMessage(response.response.content);
            
            // 更新会话状态
            if (response.session_update) {
              setConversationState(prev => ({
                ...prev,
                sessionState: response.session_update.updated_session_state
              }));
            }
          } else {
            // Fallback message
            await addTypingMessage('太好了！我已经分析了您的简历。现在让我了解一下您的留学目标和职业规划。');
          }
        } catch (error) {
          console.error('Error processing CV upload:', error);
          await addTypingMessage('简历分析完成！请告诉我您希望在新西兰学习什么专业？');
        }

        } else {
          // CV分析失败
          console.error('CV分析失败:', analysisResponse);
          addMessage({
            type: 'system',
            content: `CV分析失败: ${analysisResponse.error || '分析过程出错'}`
          });
          
          // 仍然设置为已上传，允许继续对话
          setConversationState(prev => ({
            ...prev,
            cvUploaded: true,
            sessionState: {
              ...prev.sessionState,
              cv_uploaded: true,
              cv_analysis_completed: false
            }
          }));
        }

      } else {
        console.error('CV上传失败:', uploadResponse);
        addMessage({
          type: 'system',
          content: `上传失败: ${uploadResponse.error || '未知错误'}`
        });
      }
    } catch (error) {
      console.error('CV上传出错:', error);
      addMessage({
        type: 'system',
        content: `上传出错: ${error instanceof Error ? error.message : String(error)}`
      });
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
    }
  };

  // 处理用户回答
  const handleUserAnswer = async () => {
    if (!currentInput.trim()) return;

    // 添加用户消息
    addMessage({
      type: 'user',
      content: currentInput
    });

    const userMessage = currentInput;
    setCurrentInput('');
    setIsLoading(true);

    try {
      // 准备对话历史
      const conversationHistory = {
        messages: messages.map(msg => ({
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp.toISOString()
        }))
      };

      // 调用智能对话API
      const response = await apiCall('/api/qa-assistant/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          conversation_history: conversationHistory,
          user_message: userMessage,
          cv_analysis: conversationState.cvAnalysis || {},
          session_state: conversationState.sessionState
        })
      });

      if (response.success && response.response) {
        const aiResponse = response.response;
        
        // 更新会话状态
        if (response.session_update) {
          setConversationState(prev => ({
            ...prev,
            sessionState: response.session_update.updated_session_state,
            isComplete: aiResponse.conversation_complete || false,
            isGeneratingReport: aiResponse.action === 'generate_report'
          }));
        }

        // 处理不同类型的响应
        if (aiResponse.response_type === 'final_report') {
          // 显示最终报告完成消息
          await addTypingMessage('🎉 您的个性化留学建议报告已生成完成！');
          
          // 生成PDF报告并提供下载
          try {
            const reportResponse = await apiCall('/api/qa-assistant/generate-report', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                cv_analysis: conversationState.cvAnalysis || {},
                conversation_history: messages.reduce((acc, msg) => {
                  if (msg.type === 'user') {
                    acc[`message_${msg.id}`] = msg.content;
                  }
                  return acc;
                }, {} as { [key: string]: string }),
                user_id: user?.id,
                report_content: aiResponse.content,
                matched_programs: aiResponse.matched_programs || []
              })
            });

            if (reportResponse.success) {
              // 显示下载链接
              addMessage({
                type: 'assistant',
                content: `📄 您的个性化留学建议报告已准备就绪！\n\n点击下载: ${reportResponse.report_url}`
              });
            } else {
              // 显示报告内容（如果PDF生成失败）
              addMessage({
                type: 'assistant', 
                content: '报告内容：\n\n' + aiResponse.content.substring(0, 1000) + '...\n\n(PDF生成失败，显示文本版本)'
              });
            }
          } catch (error) {
            console.error('报告生成失败:', error);
            // 显示报告内容作为fallback
            addMessage({
              type: 'assistant',
              content: '📋 您的留学建议报告：\n\n' + aiResponse.content.substring(0, 1000) + '...\n\n(完整报告请联系顾问获取)'
            });
          }
          
        } else if (aiResponse.response_type === 'generating_report') {
          // 显示报告生成中
          await addTypingMessage(aiResponse.content);
          setConversationState(prev => ({ ...prev, isGeneratingReport: true }));
          
          // 开始生成报告
          await generateReport();
          
        } else {
          // 直接显示AI回应（现在是纯文本问题）
          await addTypingMessage(aiResponse.content);
        }

      } else {
        // 错误处理
        await addTypingMessage('抱歉，我在处理您的消息时遇到了问题。请重新告诉我您的需求。');
      }

    } catch (error) {
      console.error('Error processing user answer:', error);
      await addTypingMessage('网络连接出现问题，请稍后重试。');
    } finally {
      setIsLoading(false);
    }
  };

  // 生成报告
  const generateReport = async () => {
    try {
      // 准备对话历史
      const conversationHistory = messages.reduce((acc, msg) => {
        if (msg.type === 'user') {
          acc[`message_${msg.id}`] = msg.content;
        }
        return acc;
      }, {} as { [key: string]: string });

      // 调用后端API生成报告
      const response = await apiCall('/api/qa-assistant/generate-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cv_analysis: conversationState.cvAnalysis,
          conversation_history: conversationHistory,
          user_id: user?.id
        })
      });

      if (response.success) {
        await addTypingMessage(`报告生成完成！我已经为您准备了一份详细的留学建议报告，包含了最适合您的3个项目推荐。`);
        
        // 显示下载链接
        addMessage({
          type: 'assistant',
          content: `📄 点击下载您的个性化留学建议报告: [下载PDF报告](${response.report_url})`
        });
        
        setConversationState(prev => ({
          ...prev,
          isComplete: true,
          isGeneratingReport: false
        }));
      } else {
        await addTypingMessage('抱歉，报告生成过程中出现了问题，请稍后重试。');
        setConversationState(prev => ({ ...prev, isGeneratingReport: false }));
      }
    } catch (error) {
      await addTypingMessage('报告生成失败，请稍后重试。');
      setConversationState(prev => ({ ...prev, isGeneratingReport: false }));
    }
  };

  // 处理文件选择
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  // 渲染消息
  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    
    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-blue-500 text-white'
              : isSystem
              ? 'bg-red-100 text-red-800 border border-red-300'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          <div className="text-sm">
            {message.content}
            {message.isTyping && (
              <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse"></span>
            )}
          </div>
          <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  // 渲染当前输入区域
  const renderInputArea = () => {
    if (conversationState.isComplete && !conversationState.isGeneratingReport) {
      return (
        <div className="text-center text-gray-500">
          对话已完成，感谢您的参与！
        </div>
      );
    }

    if (conversationState.isGeneratingReport) {
      return (
        <div className="text-center text-gray-500">
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
            <span>正在生成您的个性化留学报告...</span>
          </div>
        </div>
      );
    }

    // 如果还没有上传CV，显示上传选项
    if (!conversationState.cvUploaded) {
      return (
        <div className="space-y-4">
          {/* CV上传区域 */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="mt-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-purple-600 hover:text-purple-500 font-medium"
                  disabled={isLoading}
                >
                  点击上传简历
                </button>
                <p className="text-xs text-gray-500 mt-1">支持 PDF, DOC, DOCX 格式</p>
              </div>
            </div>
            {selectedFile && (
              <div className="mt-3 text-center">
                <span className="text-sm text-gray-600">已选择: {selectedFile.name}</span>
                <button
                  onClick={handleCVUpload}
                  disabled={isLoading}
                  className="ml-3 px-4 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors disabled:bg-gray-300 text-sm"
                >
                  {isLoading ? '分析中...' : '上传分析'}
                </button>
              </div>
            )}
          </div>
          
          {/* 文本输入区域 */}
          <div className="flex space-x-2">
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleUserAnswer()}
              placeholder="或者直接告诉我您的留学需求..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <button
              onClick={handleUserAnswer}
              disabled={isLoading || !currentInput.trim()}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:bg-gray-300"
            >
              {isLoading ? '...' : '发送'}
            </button>
          </div>
        </div>
      );
    }

    // 正常对话阶段
    return (
      <div className="flex space-x-2">
        <input
          type="text"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleUserAnswer()}
          placeholder="请输入您的回答..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          disabled={isLoading}
        />
        <button
          onClick={handleUserAnswer}
          disabled={isLoading || !currentInput.trim()}
          className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:bg-gray-300"
        >
          {isLoading ? '...' : '发送'}
        </button>
      </div>
    );
  };

  return (
    <div className="flex-1 max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-4">
          <div className="flex items-center">
            <svg className="w-6 h-6 mr-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <h2 className="text-xl font-bold text-white">QA助手</h2>
          </div>
          <p className="text-purple-100 text-sm mt-1">
            智能对话式留学咨询，为您量身定制专业建议
          </p>
        </div>

        {/* Chat Messages */}
        <div className="h-96 overflow-y-auto p-6 bg-gray-50">
          {messages.map(renderMessage)}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white border-t border-gray-200">
          {renderInputArea()}
          
          {/* Conversation Status */}
          {conversationState.sessionState && conversationState.sessionState.completion_score > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>信息收集进度</span>
                <span>{Math.round(conversationState.sessionState.completion_score)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${conversationState.sessionState.completion_score}%` }}
                ></div>
              </div>
              {conversationState.sessionState.completion_score >= 75 && (
                <p className="text-xs text-green-600 mt-1">信息收集充足，准备生成个性化建议！</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
