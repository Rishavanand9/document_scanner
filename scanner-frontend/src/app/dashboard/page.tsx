'use client'

import Link from 'next/link'
import { useState } from 'react'
import AnalysisResults from './AnalysisResults';
import Camera from './Camera';

export default function Dashboard() {
    const [isCameraOpen, setIsCameraOpen] = useState(false)
    const [capturedVideo, setCapturedVideo] = useState<string | null>(null)
    const [analysisResults, setAnalysisResults] = useState<any>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [rawJsonResponse, setRawJsonResponse] = useState<string>('');

    const handleCapture = (videoBlob: string) => {
        setCapturedVideo(videoBlob)
        setIsCameraOpen(false)
    }

    const handleAuthenticate = async () => {
        if (!capturedVideo) return;

        setIsAnalyzing(true);
        setRawJsonResponse('');
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
            setRawJsonResponse(JSON.stringify(results, null, 2));
        } catch (error: unknown) {
            console.error('Authentication error:', error);
            setRawJsonResponse(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }, null, 2));
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const videoUrl = URL.createObjectURL(file);
            setCapturedVideo(videoUrl);
            setIsCameraOpen(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <nav className="bg-white shadow-md border-b border-gray-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">Dashboard</h1>
                        </div>
                        <div className="flex items-center">
                            <Link
                                href="/"
                                className="text-gray-600 hover:text-blue-600 transition-colors duration-200 font-medium"
                            >
                                Logout
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="border-2 border-gray-200 rounded-xl bg-white shadow-lg min-h-[600px] flex flex-col items-center justify-center p-8">
                        {!isCameraOpen && !capturedVideo && (
                            <button
                                onClick={() => setIsCameraOpen(true)}
                                className="bg-blue-600 text-white px-8 py-4 rounded-lg hover:bg-blue-700 transition-all duration-200 text-lg font-medium shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
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

                        <div className="mt-4 flex flex-col items-center">
                            <input
                                type="file"
                                accept="video/*"
                                onChange={handleFileUpload}
                                className="mb-4 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                            />
                            {capturedVideo && (
                                <div className="mt-6 flex gap-4">
                                    <button
                                        onClick={() => {
                                            setCapturedVideo(null);
                                            setAnalysisResults(null);
                                            setIsCameraOpen(true);
                                        }}
                                        className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-all duration-200 shadow-md hover:shadow-lg"
                                    >
                                        Record Again
                                    </button>
                                    <button
                                        onClick={handleAuthenticate}
                                        disabled={isAnalyzing}
                                        className={`${
                                            isAnalyzing ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'
                                        } text-white px-6 py-3 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg`}
                                    >
                                        {isAnalyzing ? 'Analyzing...' : 'Authenticate Video'}
                                    </button>
                                </div>
                            )}

                            {isAnalyzing && (
                                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                                    <div className="bg-white p-8 rounded-xl shadow-2xl flex flex-col items-center">
                                        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-600 mb-4"></div>
                                        <p className="text-lg font-medium text-gray-700">Analyzing Video...</p>
                                        <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
                                    </div>
                                </div>
                            )}

                            {analysisResults && (
                                <>
                                    <AnalysisResults results={analysisResults} />
                                    <div className="mt-8">
                                        <h3 className="text-xl font-semibold mb-4 text-gray-700">Raw Response</h3>
                                        <div className="bg-gray-900 rounded-lg p-4 overflow-x-scroll ">
                                            <span>
                                                {rawJsonResponse}
                                            </span>
                                        </div> 
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
