// src/App.js

import { useState, useEffect, useRef } from 'react';
// --- No change to imports, but we'll use X to remove the preview ---
import { Plus, Send, ChevronDown, ChevronUp, X } from 'lucide-react';

// --- Helper Components ---
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

const ChatMessage = ({ message }) => {
  const isAi = message.sender === 'ai';
  return (
    <div className={`flex mb-4 ${isAi ? 'justify-start' : 'justify-end'}`}>
      <div 
        className={`rounded-lg px-4 py-2 max-w-2xl shadow-md ${isAi ? 'bg-gray-700 text-white' : 'bg-blue-600 text-white'}`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
      </div>
    </div>
  );
};

const ThinkingProcess = ({ steps, isExpanded, setIsExpanded }) => {
  if (steps.length === 0) return null;

  return (
    <div className="flex justify-center mb-4">
      <div className="w-full max-w-2xl bg-gray-800 bg-opacity-50 rounded-lg p-3">
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex justify-between items-center text-gray-300 hover:text-white"
        >
          <span>Consulting Experts...</span>
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        {isExpanded && (
          <div className="mt-3 border-t border-gray-600 pt-3 space-y-2">
            {steps.map(step => (
              <div key={step.id} className="text-sm text-gray-400 flex items-start animate-pulse">
                <span className="mr-2">{AGENT_EMOJIS[step.agent_name] || AGENT_EMOJIS.default}</span>
                <span><strong>{step.agent_name}</strong> is working...</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};


// --- Main App Component ---
function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai" },
  ]);
  const [thinkingSteps, setThinkingSteps] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const [input, setInput] = useState('');
  
  // --- MODIFIED: State to hold the image file AND its preview URL ---
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const fileInputRef = useRef(null);
  
  const socket = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    connect();
    return () => {
      if (socket.current) socket.current.close();
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingSteps]);


  const connect = () => {
    socket.current = new WebSocket('ws://127.0.0.1:8000/ws/chat');
    socket.current.onopen = () => console.log("WebSocket connected!");
    socket.current.onclose = () => console.log("WebSocket disconnected.");

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'agent_step':
          setIsThinking(true);
          setThinkingSteps(prev => [...prev, { agent_name: data.agent_name, id: Date.now() }]);
          break;
        case 'final_answer':
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setThinkingSteps([]);
          break;
        case 'error':
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setThinkingSteps([]);
          break;
        default:
          console.warn("Received unknown message type:", data.type);
      }
    };
  };

  // --- MODIFIED: Handler to create and manage image previews ---
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);
    } else {
      setImageFile(null);
      setImagePreview('');
    }
  };
  
  const removeImage = () => {
    setImageFile(null);
    setImagePreview('');
    // Important: Revoke the object URL to free up memory
    if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
    }
  }

  const handlePlusClick = () => {
    fileInputRef.current.click();
  };

  const handleSend = () => {
    if (isThinking || (!input.trim() && !imageFile)) return;
    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) return;

    let messageText = input;
    if (imageFile) {
        // Just indicating an image is attached for now
        messageText = `[Image Attached: ${imageFile.name}] \n\n${input}`;
    }

    setMessages(prev => [...prev, { id: Date.now(), text: messageText, sender: 'user' }]);
    
    // For now, we still just send the text. The backend doesn't handle the file yet.
    socket.current.send(input);
    
    setInput('');
    removeImage(); // Use our new cleanup function
    setIsThinking(true);
    setThinkingSteps([]);
    setIsThinkingExpanded(true);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !isThinking) handleSend();
  };


  return (
    <div className="bg-[#131314] h-screen flex flex-col text-white font-sans">
      <header className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-semibold">🌾 Charlie 1.0 - Agricultural Advisor</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          <ThinkingProcess 
            steps={thinkingSteps} 
            isExpanded={isThinkingExpanded}
            setIsExpanded={setIsThinkingExpanded}
          />
          
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
        
          {/* --- MODIFIED: UI to show an image preview --- */}
          {imagePreview && (
            <div className="bg-gray-700 bg-opacity-50 rounded-md p-2 mb-2 flex items-center justify-between text-sm relative w-24 h-24">
              <img src={imagePreview} alt="Selected preview" className="w-full h-full object-cover rounded-md" />
              <button onClick={removeImage} className="absolute top-1 right-1 p-1 bg-black bg-opacity-50 hover:bg-opacity-75 rounded-full">
                <X size={16} />
              </button>
            </div>
          )}

          <div className="bg-[#1e1f20] rounded-full flex items-center p-2 border border-gray-700">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileSelect}
              className="hidden"
              accept="image/*"
            />
            <button onClick={handlePlusClick} className="p-2 text-gray-400 hover:text-white rounded-full transition-colors">
              <Plus size={24} />
            </button>
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
              disabled={(!input.trim() && !imageFile) || isThinking}
            >
              <Send size={24} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
