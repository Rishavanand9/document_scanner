'use client'

import Link from 'next/link'
import { useState, useRef, useEffect } from 'react'

export default function Dashboard() {
  const [isCameraOpen, setIsCameraOpen] = useState(false)
  const [capturedVideo, setCapturedVideo] = useState<string | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<Array<{
    frame_number: number;
    timestamp: number;
    caption: string;
  }> | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleCapture = (videoBlob: string) => {
    setCapturedVideo(videoBlob)
    setIsCameraOpen(false)
  }

  const handleAuthenticate = async () => {
    if (!capturedVideo) return;

    setIsAnalyzing(true);
    try {
      // Convert the video URL to a File object
      const response = await fetch(capturedVideo);
      const blob = await response.blob();
      const file = new File([blob], 'video.mp4', { type: 'video/mp4' });

      // Create FormData and append the file
      const formData = new FormData();
      formData.append('file', file);

      // Make API call
      const apiResponse = await fetch('http://127.0.0.1:8000/api/authenticate', {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        throw new Error('Authentication failed');
      }

      const results = await apiResponse.json();
      setAnalysisResults(results);
    } catch (error) {
      console.error('Authentication error:', error);
      // You might want to show an error message to the user here
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Dashboard</h1>
            </div>
            <div className="flex items-center">
              <Link 
                href="/" 
                className="text-gray-600 hover:text-gray-900"
              >
                Logout
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg min-h-[600px] flex flex-col items-center justify-center">
            {!isCameraOpen && !capturedVideo && (
              <button
                onClick={() => setIsCameraOpen(true)}
                className="bg-blue-500 text-white px-6 py-3 rounded-md hover:bg-blue-600 transition-colors text-lg"
              >
                Start Recording
              </button>
            )}
            
            {isCameraOpen && (
              <Camera 
                onCapture={handleCapture} 
                onClose={() => setIsCameraOpen(false)}
              />
            )}

            {capturedVideo && (
              <div className="mt-4 flex flex-col items-center">
                <video 
                  src={capturedVideo} 
                  controls 
                  className="w-full max-w-4xl rounded-lg"
                />
                <div className="mt-6 flex gap-4">
                  <button
                    onClick={() => {
                      setCapturedVideo(null);
                      setAnalysisResults(null);
                      setIsCameraOpen(true);
                    }}
                    className="bg-gray-500 text-white px-6 py-3 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    Record Again
                  </button>
                  <button
                    onClick={handleAuthenticate}
                    disabled={isAnalyzing}
                    className={`${
                      isAnalyzing ? 'bg-gray-400' : 'bg-green-500 hover:bg-green-600'
                    } text-white px-6 py-3 rounded-md transition-colors`}
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Authenticate Video'}
                  </button>
                </div>

                {/* Display analysis results */}
                {analysisResults && (
                  <div className="mt-6 w-full max-w-4xl">
                    <h2 className="text-xl font-bold mb-4">Analysis Results</h2>
                    <div className="bg-white shadow rounded-lg p-4">
                      <div className="space-y-2">
                        {analysisResults.map((result) => (
                          <div 
                            key={result.frame_number}
                            className="p-3 bg-gray-50 rounded flex justify-between"
                          >
                            <span>Frame: {result.frame_number}</span>
                            <span>Time: {result.timestamp.toFixed(2)}s</span>
                            <span>Caption: {result.caption}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function Camera({ onCapture, onClose }: { onCapture: (videoBlob: string) => void; onClose: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const chunksRef = useRef<Blob[]>([])

  useEffect(() => {
    let stream: MediaStream | null = null

    async function setupCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            aspectRatio: 16/9 
          },
          audio: true 
        })
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          mediaRecorderRef.current = new MediaRecorder(stream)
          
          mediaRecorderRef.current.ondataavailable = (event) => {
            if (event.data.size > 0) {
              chunksRef.current.push(event.data)
            }
          }

          mediaRecorderRef.current.onstop = () => {
            const blob = new Blob(chunksRef.current, { type: 'video/webm' })
            const videoUrl = URL.createObjectURL(blob)
            onCapture(videoUrl)
            chunksRef.current = []
          }
        }
      } catch (err) {
        console.error('Error accessing camera:', err)
      }
    }

    setupCamera()

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [onCapture])

  const startRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.start()
      setIsRecording(true)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  return (
    <div className="relative w-full max-w-4xl">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full rounded-lg"
      />
      <div className="mt-4 flex gap-4 justify-center">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="bg-red-500 text-white px-6 py-3 rounded-md hover:bg-red-600 transition-colors"
          >
            Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="bg-gray-500 text-white px-6 py-3 rounded-md hover:bg-gray-600 transition-colors"
          >
            Stop Recording
          </button>
        )}
        <button
          onClick={onClose}
          className="bg-red-500 text-white px-6 py-3 rounded-md hover:bg-red-600 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  )
}