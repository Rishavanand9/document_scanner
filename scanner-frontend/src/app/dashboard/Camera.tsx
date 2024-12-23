import { useEffect, useRef, useState } from "react";

interface CameraProps {
    onCapture: (videoBlob: Blob) => void;
    onClose: () => void;
}

export default function Camera({ onCapture, onClose }: CameraProps) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const [isRecording, setIsRecording] = useState(false)
    const chunksRef = useRef<Blob[]>([])
    const [videoBlob, setVideoBlob] = useState<Blob | null>(null)

    useEffect(() => {
        let stream: MediaStream | null = null

        async function setupCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 1920 },
                        height: { ideal: 1080 },
                        aspectRatio: 16 / 9
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
                        setVideoBlob(blob)
                        // const videoUrl = URL.createObjectURL(blob)
                        onCapture(blob)
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

    const handleDownload = () => {
        if (videoBlob) {
            const url = URL.createObjectURL(videoBlob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'recorded-video.webm'
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        }
    }

    return (
        <div className="relative w-full max-w-4xl">
            <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full rounded-xl shadow-lg"
            />
            <div className="mt-6 flex gap-4 justify-center">
                {!isRecording ? (
                    <button
                        onClick={startRecording}
                        className="bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                    >
                        Start Recording
                    </button>
                ) : (
                    <button
                        onClick={stopRecording}
                        className="bg-gray-600 text-white px-8 py-3 rounded-lg hover:bg-gray-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                    >
                        Stop Recording
                    </button>
                )}
                {videoBlob && !isRecording && (
                    <button
                        onClick={handleDownload}
                        className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                    >
                        Download Video
                    </button>
                )}
                <button
                    onClick={onClose}
                    className="bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                >
                    Close
                </button>
            </div>
        </div>
    )
}