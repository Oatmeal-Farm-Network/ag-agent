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
        {/* Display images if present */}
        {message.images && message.images.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {message.images.map((img, index) => (
              <img 
                key={index}
                src={img.preview} 
                alt={`Uploaded image ${index + 1}`}
                className="max-w-32 max-h-32 object-cover rounded"
              />
            ))}
          </div>
        )}
        
        {/* Display text */}
        {message.text && (
          <p className="whitespace-pre-wrap">{message.text}</p>
        )}
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
  // --- ADDED: State for multiple images ---
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageLimitError, setImageLimitError] = useState('');
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


  // This is the new, corrected function
const connect = () => {
    // Determine the correct protocol. If the website is loaded via https://,
    // we must use the secure websocket protocol wss://
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // Get the current hostname (e.g., multi-container-agent-app.eastus.azurecontainerapps.io)
    const host = window.location.host;
    
    // Define the path to our websocket endpoint. Nginx will handle this.
    const path = '/ws/chat';

    const wsUrl = `${protocol}//${host}${path}`;

    console.log(`Attempting to connect to WebSocket at: ${wsUrl}`);

    socket.current = new WebSocket(wsUrl);

    socket.current.onopen = () => console.log("WebSocket connected!");
    socket.current.onclose = () => console.log("WebSocket disconnected.");

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received message:", data);
      
      switch (data.type) {
        case 'agent_step':
          setIsThinking(true);
          setThinkingSteps(prev => [...prev, { agent_name: data.agent_name, id: Date.now() }]);
          break;
          
        case 'final_answer':
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          
          setTimeout(() => {
            setIsThinking(false);
            setIsThinkingExpanded(false);
            setThinkingSteps([]);
            console.log("Thinking UI cleared after final answer");
          }, 500);
          break;
          
        case 'error':
          setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setIsThinkingExpanded(false);
          setThinkingSteps([]);
          break;
          
        default:
          console.warn("Received unknown message type:", data.type);
      }
    };
};
  
  // --- MODIFIED: Handler to create and manage image previews ---
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    if (selectedImages.length + files.length > 5) {
      setImageLimitError('You can only upload up to 5 images at a time.');
      setTimeout(() => setImageLimitError(''), 3000);
      return;
    }
    
    const newImages = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setSelectedImages(prev => [...prev, ...newImages]);
    event.target.value = '';
  };
  
  const removeImage = (id) => {
    setSelectedImages(prev => {
      const img = prev.find(img => img.id === id);
      if (img) URL.revokeObjectURL(img.preview);
      return prev.filter(img => img.id !== id);
    });
  };

  const clearAllImages = () => {
    selectedImages.forEach(img => URL.revokeObjectURL(img.preview));
    setSelectedImages([]);
  };

  const handlePlusClick = () => {
    if (selectedImages.length >= 5) {
      setImageLimitError('You can only upload up to 5 images at a time.');
      setTimeout(() => setImageLimitError(''), 3000);
      return;
    }
    fileInputRef.current.click();
  };

  const handleSend = async () => {
    if (isThinking || (!input.trim() && selectedImages.length === 0)) return;
    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) return;

    // Convert images to base64
    const imageData = [];
    const messageImages = [];
    
    if (selectedImages.length > 0) {
      for (const img of selectedImages) {
        try {
          const base64 = await fileToBase64(img.file);
          imageData.push({
            name: img.file.name,
            type: img.file.type,
            data: base64
          });
          
          // Create data URL for message display
          const dataUrl = `data:${img.file.type};base64,${base64}`;
          messageImages.push({
            id: img.id,
            preview: dataUrl
          });
        } catch (error) {
          console.error('Error converting image to base64:', error);
        }
      }
    }

    // Create payload
    const payload = {
      type: "multimodal_query",
      text: input,
      images: imageData,
      user_id: "user123" // You can generate this dynamically
    };

    // Display message in UI with images
    const messageData = {
      id: Date.now(),
      text: input,
      sender: 'user',
      images: messageImages.length > 0 ? messageImages : undefined
    };
    
    setMessages(prev => [...prev, messageData]);

    // Send payload to backend
    socket.current.send(JSON.stringify(payload));

    setInput('');
    clearAllImages();
    setIsThinking(true);
    setThinkingSteps([]);
    setIsThinkingExpanded(true);
  };

  // Helper function to convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:image/...;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
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
        
          {/* --- MODIFIED: UI to show multiple image previews --- */}
          {selectedImages.length > 0 && (
            <div className="mb-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''} uploaded</span>
                <button onClick={clearAllImages} className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded">Clear All</button>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedImages.map(img => (
                  <div key={img.id} className="relative">
                    <img src={img.preview} alt="Preview" className="w-16 h-16 object-cover rounded" />
                    <button
                      onClick={() => removeImage(img.id)}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          {imageLimitError && (
            <div className="text-xs text-red-400 mb-2">{imageLimitError}</div>
          )}

          <div className="bg-[#1e1f20] rounded-full flex items-center p-2 border border-gray-700">
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden"
              accept="image/*"
              multiple
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
              disabled={(!input.trim() && selectedImages.length === 0) || isThinking}
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