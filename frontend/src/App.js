import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Plus, Send, ChevronDown, ChevronUp, X, Mic, MessageCircle, Volume2, Loader2 } from 'lucide-react';
import useUserId from './useUserId';

if (process.env.NODE_ENV === 'production' && !process.env.REACT_APP_BACKEND_HOST) {
  throw new Error("FATAL: REACT_APP_BACKEND_HOST environment variable is not set for the production build.");
}

// All your helper components (SpeakerIcon, useSpeechSynthesis, ChatMessage, etc.) remain unchanged.
const SpeakerIcon = ({ isSpeaking, onClick }) => ( <svg onClick={onClick} className={`w-5 h-5 cursor-pointer transition-colors duration-200 ${isSpeaking ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" /></svg>);
const useSpeechSynthesis = () => { const [speakingMessageId, setSpeakingMessageId] = useState(null); const synth = useRef(window.speechSynthesis); const handleSpeak = (message) => { const { id, text } = message; if (!text) { return; } if (synth.current.speaking && speakingMessageId === id) { synth.current.cancel(); setSpeakingMessageId(null); return; } if (synth.current.speaking) { synth.current.cancel(); } const utterance = new SpeechSynthesisUtterance(text); utterance.onstart = () => { setSpeakingMessageId(id); }; utterance.onend = () => { setSpeakingMessageId(null); }; utterance.onerror = (event) => { console.error('SpeechSynthesisUtterance.onerror', event); setSpeakingMessageId(null); }; synth.current.speak(utterance); }; useEffect(() => { const currentSynth = synth.current; return () => { if (currentSynth?.speaking) { currentSynth.cancel(); } }; }, []); return { speakingMessageId, handleSpeak }; };
const AGENT_EMOJIS = {"SemanticSearcher": "🔍","ContextProcessor": "📋","SoilScienceSpecialist": "🌱","PlantNutritionExpert": "🧪","LeadAgriculturalAdvisor": "👨‍🌾","WeatherSpecialist": "🌦️","LivestockBreedSpecialist": "🐄","Farmer_Query_Relay": "👤","default": "🤖"};
const ChatMessage = ({ message, onSpeak, isSpeaking }) => { const isAi = message.sender === 'ai'; return ( <div className={`flex mb-4 ${isAi ? 'flex-col items-start' : 'justify-end'}`}> <div className={`rounded-lg px-4 py-2 max-w-2xl shadow-md ${isAi ? 'bg-gray-700 text-white' : 'bg-blue-600 text-white'}`}> {message.images && message.images.length > 0 && ( <div className="mb-3 flex flex-wrap gap-2"> {message.images.map((img, index) => ( <img key={index} src={img.preview} alt={`Uploaded image ${index + 1}`} className="max-w-32 max-h-32 object-cover rounded" /> ))} </div> )} {message.text && ( <p className="whitespace-pre-wrap">{message.text}</p> )} </div> {isAi && message.text && ( <div className="flex items-center gap-3 mt-2"> <SpeakerIcon isSpeaking={isSpeaking} onClick={() => onSpeak(message)} /> </div> )} </div> ); };
const ThinkingProcess = ({ steps, isExpanded, setIsExpanded }) => { if (steps.length === 0) return null; return ( <div className="flex justify-center mb-4"> <div className="w-full max-w-2xl bg-gray-800 bg-opacity-50 rounded-lg p-3"> <button onClick={() => setIsExpanded(!isExpanded)} className="w-full flex justify-between items-center text-gray-300 hover:text-white"> <span>Consulting Experts...</span> {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />} </button> {isExpanded && ( <div className="mt-3 border-t border-gray-600 pt-3 space-y-2"> {steps.map(step => ( <div key={step.id} className="text-sm text-gray-400 flex items-start animate-pulse"> <span className="mr-2">{AGENT_EMOJIS[step.agent_name] || AGENT_EMOJIS.default}</span> <span><strong>{step.agent_name}</strong> is working...</span> </div> ))} </div> )} </div> </div> ); };
const ConnectionStatus = ({ isConnected, isConnecting }) => { if (isConnected) return null; return ( <div className="flex justify-center mb-4"> <div className="bg-yellow-600 bg-opacity-80 text-white px-4 py-2 rounded-lg text-sm"> {isConnecting ? "Connecting to server..." : "⚠️ Connection lost. Attempting to reconnect..."} </div> </div> ); };
const VoiceChat = React.forwardRef(({ onStart, onStop, onVolumeChange, className, demoMode = true, autoStart = false, userId }, ref) => { const [isListening, setIsListening] = useState(false); const [isProcessing, setIsProcessing] = useState(false); const [isSpeaking, setIsSpeaking] = useState(false); const [waveformData, setWaveformData] = useState(Array(32).fill(0)); const intervalRef = useRef(); const mediaRecorderRef = useRef(null); const audioContextRef = useRef(null); const analyserRef = useRef(null); const microphoneRef = useRef(null); const audioStreamRef = useRef(null); const silenceTimerRef = useRef(null); React.useImperativeHandle(ref, () => ({ stopListening: () => { setIsListening(false); stopAudioRecording(); }, handleVoiceResponse: (data) => { setIsProcessing(false); setIsSpeaking(true); if (data.audio) { playAudioResponse(data.audio); } else { speakText(data.text); } }, stopAudioPlayback: () => { stopAudioPlayback(); } })); useEffect(() => { if (isListening) { startAudioRecording(); } else { stopAudioRecording(); } return () => stopAudioRecording(); }, [isListening]); const startAudioRecording = async () => { try { const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); audioStreamRef.current = stream; const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); mediaRecorderRef.current = mediaRecorder; const audioContext = new (window.AudioContext || window.webkitAudioContext)(); audioContextRef.current = audioContext; const analyser = audioContext.createAnalyser(); analyserRef.current = analyser; analyser.fftSize = 64; const microphone = audioContext.createMediaStreamSource(stream); microphoneRef.current = microphone; microphone.connect(analyser); mediaRecorder.ondataavailable = (event) => {}; mediaRecorder.start(); const dataArray = new Uint8Array(analyser.frequencyBinCount); intervalRef.current = setInterval(() => { analyser.getByteFrequencyData(dataArray); setWaveformData(Array(32).fill(0).map((_, i) => dataArray[Math.floor(i*dataArray.length/32)]||0));}, 100); onStart?.(); } catch (error) {console.error('Error starting audio recording:', error);}}; const stopAudioRecording = () => { if (intervalRef.current) clearInterval(intervalRef.current); if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current); if (mediaRecorderRef.current) mediaRecorderRef.current.stop(); if (microphoneRef.current) microphoneRef.current.disconnect(); if (audioContextRef.current) audioContextRef.current.close(); if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach(track => track.stop()); setWaveformData(Array(32).fill(0)); onStop?.(0); }; const handleToggleListening = () => { if (isListening) { setIsListening(false); setIsProcessing(true); onStop?.(0); if (mediaRecorderRef.current) { mediaRecorderRef.current.stop(); mediaRecorderRef.current.ondataavailable = async (event) => { if (event.data.size > 0) { const audioBlob = new Blob([event.data], { type: 'audio/webm' }); const base64 = await blobToBase64(audioBlob); if (window.socket && window.socket.readyState === WebSocket.OPEN) { window.socket.send(JSON.stringify({ type: 'voice_conversation', audio: base64, audio_format: 'webm', user_id: userId })); } } }; } } else { setIsListening(true); onStart?.(); } }; const blobToBase64 = (blob) => new Promise((resolve, reject) => { const reader = new FileReader(); reader.readAsDataURL(blob); reader.onloadend = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; }); const playAudioResponse = (audioBase64) => { try { const audioBlob = new Blob([Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))], { type: 'audio/wav' }); const audioUrl = URL.createObjectURL(audioBlob); const audio = new Audio(audioUrl); audio.onended = () => { setIsSpeaking(false); URL.revokeObjectURL(audioUrl); }; audio.play(); } catch (error) { setIsSpeaking(false); } }; const stopAudioPlayback = () => { if ('speechSynthesis' in window) speechSynthesis.cancel(); setIsSpeaking(false); }; const speakText = (text) => { if ('speechSynthesis' in window) { const utterance = new SpeechSynthesisUtterance(text); utterance.onend = () => setIsSpeaking(false); speechSynthesis.speak(utterance); } else { setIsSpeaking(false); } }; const getStatusText = () => { if (isListening) return "Listening..."; if (isProcessing) return "Processing..."; if (isSpeaking) return "Speaking..."; return "Tap to speak"; }; return ( <div className={`flex flex-col items-center justify-center min-h-[600px] w-full relative overflow-hidden ${className || ''}`}> <div className="absolute inset-0 flex items-center justify-center"> <div className={`w-96 h-96 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 blur-3xl transition-all duration-2000 ${isListening ? 'scale-110 opacity-60' : 'scale-100 opacity-20'}`} /> </div> <div className="relative z-10 flex flex-col items-center space-y-8"> <div className="relative group"> <button onClick={handleToggleListening} className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 bg-gradient-to-br from-blue-500/20 to-blue-500/10 border-2 ${isListening ? 'border-blue-500 shadow-lg shadow-blue-500/25' : isProcessing ? 'border-yellow-500 shadow-lg shadow-yellow-500/25' : isSpeaking ? 'border-green-500 shadow-lg shadow-green-500/25' : 'border-gray-600 hover:border-blue-500/50'} group-hover:scale-105 active:scale-95`} > {isProcessing ? <Loader2 className="w-12 h-12 text-yellow-500 animate-spin" /> : isSpeaking ? <Volume2 className="w-12 h-12 text-green-500" /> : isListening ? <Mic className="w-12 h-12 text-blue-500" /> : <Mic className="w-12 h-12 text-gray-400" />} </button> {isListening && <><div className="absolute inset-0 rounded-full border-2 border-blue-500/30 animate-ping" /><div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-ping" style={{ animationDelay: '0.5s' }} /></>} </div> <div className="flex items-center justify-center space-x-1 h-16"> {waveformData.map((h, i) => <div key={i} className={`w-1 rounded-full transition-all duration-100 ${isListening ? 'bg-blue-500' : 'bg-gray-600'}`} style={{ height: `${Math.max(4, h * 0.6)}px` }} />)} </div> <p className={`text-lg font-medium transition-colors ${isListening ? "text-blue-400" : "text-gray-400"}`}>{getStatusText()}</p> </div> </div> ); });


function App() {
  const [messages, setMessages] = useState([
    { id: uuidv4(), text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai" },
  ]);
  const [thinkingSteps, setThinkingSteps] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const [input, setInput] = useState('');
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageLimitError, setImageLimitError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [showConversationModal, setShowConversationModal] = useState(false);
  const { speakingMessageId, handleSpeak } = useSpeechSynthesis();
  const userId = useUserId();
  
  // <<< CHANGE 1: Add state for the current session ID >>>
  const [sessionId, setSessionId] = useState(null);

  const fileInputRef = useRef(null);
  const socket = useRef(null);
  const chatEndRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const voiceChatRef = useRef(null);
   const isDoneProcessing = useRef(false); 
  const inputRef = useRef(null);

  useEffect(() => {
    connect();
    return () => {
      if (socket.current) {
        socket.current.close(1000, "Component unmounting");
      }
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingSteps]);

  const connect = () => {
    if (socket.current?.readyState === WebSocket.CONNECTING || socket.current?.readyState === WebSocket.OPEN) {
        return;
    }
    
    setIsConnecting(true);
    const backendHost = process.env.REACT_APP_BACKEND_HOST || 'localhost:8000';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${backendHost}/ws/chat`;
    
    socket.current = new WebSocket(wsUrl);

    socket.current.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttempts.current = 0;
        window.socket = socket.current;
    };

    socket.current.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        if (reconnectAttempts.current < 5) {
            const delay = Math.pow(2, reconnectAttempts.current) * 1000;
            setTimeout(() => {
                reconnectAttempts.current++;
                connect();
            }, delay);
        }
    };

    socket.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnecting(false);
    };

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        // <<< CHANGE 2: Handle the new 'session_created' event >>>
        case 'session_created':
          setSessionId(data.session_id);
          console.log(`New session started: ${data.session_id}`);
          break;

        case 'agent_step':
          setIsThinking(true);
          setThinkingSteps(prev => [...prev, { agent_name: data.agent_name, id: uuidv4() }]);
          break;
        
        case 'clear_agent_status':
          setThinkingSteps([]);
          break;
        
        case 'final_answer':
          setMessages(prev => [...prev, { id: uuidv4(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setIsThinkingExpanded(false);
          break;
        case 'error':
          setMessages(prev => [...prev, { id: uuidv4(), text: data.content, sender: 'ai' }]);
          setIsThinking(false);
          setIsThinkingExpanded(false);
          setThinkingSteps([]);
          break;
        case 'voice_response':
            if (voiceChatRef.current) {
                voiceChatRef.current.handleVoiceResponse(data);
            }
            break;
        default:
          console.warn("Unknown message type:", data.type);
      }
    };
  };
  
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    if (selectedImages.length + files.length > 5) {
      setImageLimitError('You can only upload up to 5 images.');
      setTimeout(() => setImageLimitError(''), 3000);
      return;
    }
    
    const newImages = files.map(file => ({
      id: uuidv4(),
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setSelectedImages(prev => [...prev, ...newImages]);
  };
  
  const removeImage = (id) => {
    setSelectedImages(prev => prev.filter(img => {
        if (img.id === id) URL.revokeObjectURL(img.preview);
        return img.id !== id;
    }));
  };

  const clearAllImages = () => {
    selectedImages.forEach(img => URL.revokeObjectURL(img.preview));
    setSelectedImages([]);
  };

  const handlePlusClick = () => {
    if (selectedImages.length >= 5) {
        setImageLimitError('You can only upload up to 5 images.');
        setTimeout(() => setImageLimitError(''), 3000);
        return;
    }
    fileInputRef.current.click();
  };

  const handleSend = async () => {
    if (isThinking || (!input.trim() && selectedImages.length === 0)) return;
    isDoneProcessing.current = false; 
    
    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) {
      setMessages(prev => [...prev, { id: uuidv4(), text: "Connection issue. Please wait or refresh.", sender: 'ai' }]);
      connect();
      return;
    }

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // The result includes a prefix like "data:image/jpeg;base64,"
        // which we remove to get just the base64 data.
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

    const messageImagesForUi = selectedImages.map(img => ({ id: img.id, preview: img.preview }));
    setMessages(prev => [...prev, { id: uuidv4(), text: input, sender: 'user', images: messageImagesForUi }]);

    const imagePayloadForBackend = await Promise.all(
        selectedImages.map(async (img) => ({
            name: img.file.name,
            type: img.file.type,
            data: await fileToBase64(img.file)
        }))
    );

    const payload = {
      type: "chat_message",
      text: input,
      images: imagePayloadForBackend,
      user_id: userId,
      // <<< CHANGE 3: Include the sessionId in the payload when sending >>>
      session_id: sessionId 
    };

    socket.current.send(JSON.stringify(payload));

    setInput('');
    clearAllImages();
    setIsThinking(true);
    setThinkingSteps([]);
    setIsThinkingExpanded(true);
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = error => reject(error);
    });
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !isThinking) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleMicClick = async () => {
    if (!isRecording) {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Audio recording is not supported in this browser.');
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new window.MediaRecorder(stream, { mimeType: 'audio/webm' });
        let chunks = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
        };
        recorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          setIsRecording(false);
          setMediaRecorder(null);
          const audioBlob = new Blob(chunks, { type: 'audio/webm' });
          const base64 = await blobToBase64(audioBlob);
          if (socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(JSON.stringify({
              type: 'audio',
              audio: base64,
              audio_format: 'webm',
              user_id: userId
            }));
          }
        };
        setIsRecording(true);
        setMediaRecorder(recorder);
        recorder.start();
      } catch (err) {
        alert('Could not start audio recording: ' + err.message);
      }
    } else {
      if (mediaRecorder) {
        mediaRecorder.stop();
      }
    }
  };

  // <<< CHANGE 4: Add a handler function for the 'New Chat' button >>>
  const handleNewChat = () => {
    setSessionId(null);
    setMessages([{ id: uuidv4(), text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai" }]);
    setIsThinking(false);
    setThinkingSteps([]);
    setSelectedImages([]);
    setInput('');
  };

  return (
    <div className="bg-[#131314] h-screen flex flex-col text-white font-sans">
      <header className="p-3 md:p-4 border-b border-gray-700 flex justify-between items-center">
        <h1 className="text-base sm:text-lg md:text-xl font-semibold truncate">🌾 Charlie 1.0 - Agricultural Advisor</h1>
        {/* <<< CHANGE 5: Add a 'New Chat' button to the header >>> */}
        <button onClick={handleNewChat} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-1 px-3 rounded-lg text-sm flex items-center transition-colors">
            <Plus size={16} className="mr-1" /> New Chat
        </button>
      </header>
      
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
          <ConnectionStatus isConnected={isConnected} isConnecting={isConnecting} />
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              onSpeak={handleSpeak}
              isSpeaking={speakingMessageId === message.id}
            />
          ))}
          {isThinking && (
            <ThinkingProcess 
              steps={thinkingSteps} 
              isExpanded={isThinkingExpanded}
              setIsExpanded={setIsThinkingExpanded}
            />
          )}
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="p-2 md:p-4">
        <div className="max-w-3xl mx-auto">
          {selectedImages.length > 0 && (
            <div className="mt-4 mb-2">
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
                            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold transition-colors">
                            ✕
                          </button>
                      </div>
                  ))}
              </div>
            </div>
          )}
          <div className="bg-[#1e1f20] rounded-xl flex items-center p-2 gap-2 border border-gray-700">
            <button onClick={handlePlusClick} className="p-2 text-gray-400 hover:text-white rounded-full transition-colors">
              <Plus size={24} />
            </button>
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} className="hidden" accept="image/*" multiple />
            <input
              type="text"
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Describe your farm problem..."
              className="flex-1 bg-transparent outline-none text-white placeholder-gray-500"
              // <<< CHANGE 6: Corrected disabled logic >>>
              disabled={isThinking}
            />
            {input.trim() === '' ? (
              <div className="flex items-center">
                <button type="button" onClick={handleMicClick} className={`p-2 rounded-full transition-colors ${isRecording ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}>
                  <Mic size={24} />
                </button>
                <button onClick={() => setShowConversationModal(true)} className="p-2 text-gray-400 hover:text-white rounded-full transition-colors">
                  <MessageCircle size={24} />
                </button>
              </div>
            ) : (
              <button onClick={handleSend} className="p-2 bg-blue-600 text-white rounded-full transition-colors" disabled={isThinking}>
                <Send size={24} />
              </button>
            )}
          </div>
        </div>
      </footer>

      {showConversationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-[#232324] rounded-2xl shadow-2xl p-12 max-w-4xl w-full min-h-[600px] flex flex-col items-center justify-center relative border border-gray-700">
            <button className="absolute top-6 right-6 text-gray-400 hover:text-white"
              onClick={() => {
                setShowConversationModal(false);
                if (voiceChatRef.current) {
                  voiceChatRef.current.stopListening();
                  voiceChatRef.current.stopAudioPlayback();
                }
              }}>
              <X size={32} />
            </button>
            <VoiceChat ref={voiceChatRef} userId={userId} demoMode={false} autoStart={true} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;