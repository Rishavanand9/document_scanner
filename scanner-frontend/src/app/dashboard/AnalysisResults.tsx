import React from 'react';

interface AnalysisResult {
    frame_number: number;
    timestamp: number;
    caption: {
        model: string;
        message: {
            content: string;
        };
    };
    frame_image: string;
}

interface AnalysisResultsProps {
    results: AnalysisResult[];
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ results }) => {
    if (!results || results.length === 0) {
        return <div>No analysis results available</div>;
    }

    return (
        <div className="mt-12 w-full max-w-4xl">
            <h2 className="text-2xl font-bold mb-8 text-gray-800 border-b pb-4">Analysis Results</h2>
            <div className="space-y-6">
                {results.map((result) => (
                    <div
                        key={result.frame_number}
                        className="bg-white rounded-xl shadow-lg p-6 mb-6 hover:shadow-xl transition-all duration-200"
                    >
                        <div className="flex flex-col md:flex-row gap-6">
                            <div className="md:w-1/3">
                                <img
                                    src={`data:image/jpeg;base64,${result.frame_image}`}
                                    alt={`Frame ${result.frame_number}`}
                                    className="w-full rounded-lg object-cover shadow-sm hover:shadow-md transition-shadow"
                                />
                            </div>
                            <div className="md:w-2/3">
                                <table className="w-full">
                                    <tbody>
                                        <tr className="border-b">
                                            <th className="py-2 text-left text-gray-600">Frame Number</th>
                                            <td className="py-2 text-left text-gray-600">{result.frame_number}</td>
                                        </tr>
                                        <tr className="border-b">
                                            <th className="py-2 text-left text-gray-600">Timestamp</th>
                                            <td className="py-2 text-left text-gray-600">{result.timestamp.toFixed(2)}s</td>
                                        </tr>
                                        <tr className="border-b">
                                            <th className="py-2 text-left text-gray-600">Message</th>
                                            <td className="py-2 text-left text-gray-600">
                                                {JSON.stringify(result.caption.message)}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AnalysisResults;  