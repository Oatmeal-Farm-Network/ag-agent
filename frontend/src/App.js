import { useState, useEffect, useRef } from 'react';
import { Plus, Send, ChevronDown, ChevronUp, User, Bot } from 'lucide-react';

// --- Helper Components ---

// Maps agent names to emojis for a friendly UI
const AGENT_EMOJIS = {
  "SemanticSearcher": "🔍",
  "ContextProcessor": "📋",
  "SoilScienceSpecialist": "🌱",
  "PlantNutritionExpert": "🧪",
  "LeadAgriculturalAdvisor": "👨‍🌾",
  "WeatherAgent": "🌦️",
  "LivestockBreedAgent": "🐄",
  "default": "🤖"
};

// Component to render a single chat bubble
const ChatMessage = ({ message }) => {
  const isAi = message.sender === 'ai';
  return (
    <div className={`flex mb-4 ${isAi ? 'justify-start' : 'justify-end'}`}>
      <div className={`flex items-start max-w-2xl ${isAi ? 'flex-row' : 'flex-row-reverse'}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isAi ? 'bg-green-600 mr-3' : 'bg-blue-600 ml-3'}`}>
          {isAi ? <Bot size={16} /> : <User size={16} />}
        </div>
        <div 
          className={`rounded-lg px-4 py-2 shadow-md ${isAi ? 'bg-gray-700 text-white' : 'bg-blue-600 text-white'}`}
        >
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>
      </div>
    </div>
  );
};

// Component to show individual agent message
const AgentMessage = ({ message }) => {
  return (
    <div className="mb-3 p-3 bg-gray-800 bg-opacity-60 rounded-lg border-l-4 border-blue-500">
      <div className="flex items-center mb-2">
        <span className="text-lg mr-2">{AGENT_EMOJIS[message.agent_name] || AGENT_EMOJIS.default}</span>
        <span className="font-semibold text-blue-300">{message.agent_name}</span>
      </div>
      <div className="text-gray-300 text-sm whitespace-pre-wrap pl-6">
        {message.content}
      </div>
    </div>
  );
};

// Updated component to display the collapsible thinking process with actual conversations
const ThinkingProcess = ({ agentMessages, isExpanded, setIsExpanded, isThinking }) => {
  if (agentMessages.length === 0 && !isThinking) return null;

  return (
    <div className="flex justify-center mb-4">
      <div className="w-full max-w-2xl bg-gray-900 bg-opacity-70 rounded-lg border border-gray-600">
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex justify-between items-center p-4 text-gray-300 hover:text-white hover:bg-gray-800 bg-opacity-50 rounded-t-lg transition-colors"
        >
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${isThinking ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
            <span className="font-medium">
              {isThinking ? 'Experts are consulting...' : `Consultation complete (${agentMessages.length} expert responses)`}
            </span>
          </div>
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {isExpanded && (
          <div className="p-4 border-t border-gray-600 max-h-96 overflow-y-auto">
            {agentMessages.length === 0 && isThinking ? (
              <div className="text-center text-gray-400 py-4">
                <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                Waiting for expert responses...
              </div>
            ) : (
              <div className="space-y-3">
                {agentMessages.map((message, index) => (
                  <AgentMessage key={index} message={message} />
                ))}
                {isThinking && (
                  <div className="text-center text-gray-400 py-2">
                    <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-1"></div>
                    <span className="text-xs">More experts consulting...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Add image preview component
const ImagePreview = ({ file, analysis, onRemove, isAnalyzing }) => {
    if (!file) return null;
    
    return (
        <div className="relative inline-block mr-2 mb-2">
            <img 
                src={URL.createObjectURL(file)} 
                alt="Preview" 
                className="w-[60px] h-[60px] object-cover rounded"
            />
            <button 
                onClick={onRemove}
                className="absolute -top-1.5 -right-1.5 w-[14px] h-[14px] bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-[10px] font-bold transition-colors"
            >
                ✕
            </button>
            
            {isAnalyzing && (
                <div className="absolute inset-0 bg-black bg-opacity-50 rounded flex items-center justify-center">
                    <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                </div>
            )}
        </div>
    );
};

// --- Main App Component ---

function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai" },
  ]);
  const [agentMessages, setAgentMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(true);
  const [input, setInput] = useState('');
  const [showDebug, setShowDebug] = useState(false); // Debug panel toggle
  const [debugMessages, setDebugMessages] = useState([]); // Debug message log
  const socket = useRef(null);
  const chatEndRef = useRef(null);
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageAnalyses, setImageAnalyses] = useState({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [imageLimitError, setImageLimitError] = useState('');
  const [showPlusTooltip, setShowPlusTooltip] = useState(false);

  useEffect(() => {
    connect();
    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentMessages]);

  const connect = () => {
    socket.current = new WebSocket('ws://127.0.0.1:8000/ws/chat');

    socket.current.onopen = () => {
      console.log("WebSocket connected!");
    };
    
    socket.current.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
    };
    
    socket.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socket.current.onmessage = (event) => {
      try {
        console.log("Received message:", event.data);
        const data = JSON.parse(event.data);
        console.log("Parsed data:", data);
        
        if (data.type === 'agent_message') {
          console.log("Adding agent message:", data.agent_name, data.content.substring(0, 50) + "...");
          setIsThinking(true);
          setAgentMessages(prev => {
            const newMessages = [...prev, {
              agent_name: data.agent_name,
              content: data.content,
              timestamp: data.timestamp || Date.now()
            }];
            console.log("Total agent messages:", newMessages.length);
            return newMessages;
          });
        } else if (data.type === 'final_answer') {
          console.log("Received final answer");
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          // Keep agent messages visible for reference
        } else if (data.type === 'error') {
          console.log("Received error:", data.content);
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setAgentMessages([]);
        } else {
          console.log("Unknown message type:", data.type);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error, event.data);
      }
    };
  };

  const handleSend = () => {
    if (!input.trim() || !socket.current || socket.current.readyState !== WebSocket.OPEN) return;

    // Send all image analyses first if available
    if (selectedImages.length > 0) {
      selectedImages.forEach(imageData => {
        const analysis = imageAnalyses[imageData.id];
        if (analysis) {
          socket.current.send(JSON.stringify({
            type: "image_analysis",
            analysis: analysis,
            imageId: imageData.id,
            session_id: "default"
          }));
        }
      });
    }
    
    // Send the actual query
    socket.current.send(JSON.stringify({
      type: "query",
      query: input,
      session_id: "default"
    }));
    
    // Add user's message to the UI
    setMessages(prev => [...prev, { 
      id: Date.now(), 
      text: input + (selectedImages.length > 0 ? `\n\n[${selectedImages.length} image${selectedImages.length !== 1 ? 's' : ''} uploaded]` : ''),
      sender: 'user' 
    }]);
    
    // Reset state
    setInput('');
    setSelectedImages([]);
    setImageAnalyses({});
    setIsThinking(true);
    setAgentMessages([]);
    setIsThinkingExpanded(true);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !isThinking) {
      handleSend();
    }
  };

  const handleImageUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    // Check if adding these files would exceed 5 images
    if (selectedImages.length + files.length > 5) {
        setImageLimitError('You can only upload up to 5 images at a time.');
        setTimeout(() => setImageLimitError(''), 3000); // Hide after 3 seconds
        return;
    }
    
    setIsAnalyzing(true);
    
    // Add new images to the array
    const newImages = files.map(file => ({
        id: Date.now() + Math.random(), // Unique ID for each image
        file: file,
        uploadedAt: new Date()
    }));
    
    setSelectedImages(prev => [...prev, ...newImages]);
    
    // Process each image
    for (const imageData of newImages) {
        const formData = new FormData();
        formData.append('file', imageData.file);
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/analyze-image', {
                method: 'POST',
                body: formData,
            });
            
            const result = await response.json();
            if (result.success) {
                setImageAnalyses(prev => ({
                    ...prev,
                    [imageData.id]: result.analysis
                }));
                
                // Send image analysis to WebSocket
                if (socket.current && socket.current.readyState === WebSocket.OPEN) {
                    socket.current.send(JSON.stringify({
                        type: "image_analysis",
                        analysis: result.analysis,
                        imageId: imageData.id,
                        session_id: "default"
                    }));
                }
            } else {
                console.error('Image analysis failed:', result.error);
            }
        } catch (error) {
            console.error('Upload failed:', error);
        }
    }
    
    setIsAnalyzing(false);
    // Clear the file input
    event.target.value = '';
  };

  const removeImage = (imageId) => {
    setSelectedImages(prev => prev.filter(img => img.id !== imageId));
    setImageAnalyses(prev => {
        const newAnalyses = { ...prev };
        delete newAnalyses[imageId];
        return newAnalyses;
    });
  };

  const clearAllImages = () => {
    setSelectedImages([]);
    setImageAnalyses({});
  };

  return (
    <div className="bg-[#131314] h-screen flex flex-col text-white font-sans">
      <header className="p-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold">🌾 Charlie 1.0 - Agricultural Advisor</h1>
            <p className="text-sm text-gray-400 mt-1">AI-powered farming consultation with expert agents</p>
          </div>
          <button 
            onClick={() => setShowDebug(!showDebug)}
            className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
          >
            {showDebug ? 'Hide Debug' : 'Show Debug'}
          </button>
        </div>
        
        {showDebug && (
          <div className="mt-4 p-3 bg-gray-800 rounded text-xs">
            <div className="text-gray-300 mb-2">Debug Log (Agent Messages: {agentMessages.length})</div>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {debugMessages.slice(-10).map((msg, idx) => (
                <div key={idx} className="text-gray-400">{msg}</div>
              ))}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          <ThinkingProcess 
            agentMessages={agentMessages}
            isExpanded={isThinkingExpanded}
            setIsExpanded={setIsThinkingExpanded}
            isThinking={isThinking}
          />
          
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          {selectedImages.length > 0 && (
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm text-gray-400">
                {selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''} uploaded
              </span>
              <button 
                onClick={clearAllImages}
                className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded"
              >
                Clear All
              </button>
            </div>
          )}
          {imageLimitError && (
            <div className="text-xs text-red-400 mb-2">{imageLimitError}</div>
          )}
          <div className="mb-2 flex flex-wrap">
            {selectedImages.map((imageData, index) => (
              <ImagePreview 
                key={imageData.id}
                file={imageData.file} 
                analysis={imageAnalyses[imageData.id]}
                isAnalyzing={isAnalyzing}
                onRemove={() => removeImage(imageData.id)}
              />
            ))}
          </div>
          <div className="bg-[#1e1f20] rounded-full flex items-center p-2 border border-gray-700">
            <div className="relative">
              <button
                onMouseEnter={() => setShowPlusTooltip(true)}
                onMouseLeave={() => setShowPlusTooltip(false)}
                onFocus={() => setShowPlusTooltip(true)}
                onBlur={() => setShowPlusTooltip(false)}
                onClick={() => {
                  if (selectedImages.length >= 5) {
                    setImageLimitError('You can only upload up to 5 images at a time.');
                    setTimeout(() => setImageLimitError(''), 3000);
                    return;
                  }
                  document.getElementById('image-upload').click();
                }}
                className="p-2 text-gray-400 hover:text-white rounded-full transition-colors"
              >
                <Plus size={24} />
              </button>
              {showPlusTooltip && (
                <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1 px-2 py-1 bg-gray-800 text-xs text-white rounded shadow z-10 whitespace-nowrap">
                  Attach Image(s)
                </div>
              )}
            </div>
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
              multiple
            />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your farm problem or ask a follow-up question..."
              className="flex-1 bg-transparent outline-none px-4 text-white placeholder-gray-500"
              disabled={isThinking}
            />
            <button 
              onClick={handleSend}
              className="p-2 text-gray-400 hover:text-white rounded-full transition-colors disabled:opacity-50"
              disabled={!input.trim() || isThinking}
            >
              <Send size={24} />
            </button>
          </div>
          {isThinking && (
            <div className="text-center text-gray-400 text-sm mt-2">
              Consulting with agricultural experts...
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}

export default App;