import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone'; // Using react-dropzone for better UX

export default function FileUpload({ onFileAnalyze, isLoading }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [fileError, setFileError] = useState('');

    const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
        setFileError('');
        setFile(null); // Reset file state
        setPreview(null); // Reset preview

        if (rejectedFiles && rejectedFiles.length > 0) {
            const firstRejection = rejectedFiles[0];
            if (firstRejection.errors) {
                const firstError = firstRejection.errors[0];
                if (firstError.code === 'file-too-large') {
                    setFileError('El archivo es demasiado grande (máx. 5MB).');
                } else if (firstError.code === 'file-invalid-type') {
                    setFileError('Tipo de archivo no válido. Por favor, selecciona una imagen (JPEG, PNG, WEBP).');
                } else {
                    setFileError(`Error con el archivo: ${firstError.message}`);
                }
            } else {
                setFileError('Archivo no aceptado. Verifica el tipo y tamaño.');
            }
            return;
        }

        if (acceptedFiles && acceptedFiles.length > 0) {
            const currentFile = acceptedFiles[0];
            setFile(currentFile);
            setPreview(URL.createObjectURL(currentFile));
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
        onDrop,
        accept: {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/webp': ['.webp'],
        },
        multiple: false,
        maxSize: 5 * 1024 * 1024, // 5MB
        noClick: true, // We'll trigger open manually or rely on drag
        noKeyboard: true,
        disabled: isLoading,
    });

    const handleSubmit = () => {
        if (file && !fileError) {
            onFileAnalyze(file);
        } else if (!file) {
            setFileError('Por favor, selecciona un archivo antes de analizar.');
        }
        // If fileError is set from onDrop, that message will be shown.
    };

    const handleRemoveFile = () => {
        setFile(null);
        setPreview(null);
        setFileError('');
    };

    return (
        <div className="space-y-4">
            <div
                {...getRootProps()}
                className={`p-6 border-2 border-dashed rounded-lg text-center cursor-pointer
                            ${isDragActive ? 'border-seentia-golden-amber bg-seentia-golden-amber/10' : 'border-gray-300 hover:border-seentia-golden-amber/70'}
                            ${isLoading ? 'opacity-60 cursor-not-allowed' : ''}
                            transition-colors duration-200 ease-in-out`}
            >
                <input {...getInputProps()} />
                {preview && file ? (
                    <div className="relative group">
                        <img src={preview} alt="Vista previa" className="mx-auto max-h-48 rounded-md shadow" />
                        {!isLoading && (
                            <button
                                onClick={(e) => { e.stopPropagation(); handleRemoveFile(); }}
                                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                                aria-label="Quitar imagen"
                            >
                                &#x2715; {/* Cross icon */}
                            </button>
                        )}
                    </div>
                ) : (
                    <div onClick={isLoading ? undefined : open} className="space-y-1"> {/* Make whole area clickable if no preview */}
                        <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <p className="text-sm text-gray-500">
                            Arrastra y suelta una imagen aquí, o{' '}
                            <span className="font-semibold text-seentia-golden-amber">haz clic para seleccionar</span>.
                        </p>
                        <p className="text-xs text-gray-500">PNG, JPG, WEBP (Máx. 5MB)</p>
                    </div>
                )}
            </div>

            {fileError && <p className="text-red-500 text-xs text-center">{fileError}</p>}

            <button
                onClick={handleSubmit}
                disabled={!file || isLoading || !!fileError}
                className="w-full bg-seentia-golden-amber text-white p-3 rounded-lg font-semibold hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
                {isLoading ? 'Analizando...' : 'Analizar Mi Rostro'}
            </button>
        </div>
    );
}
