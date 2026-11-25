import React from 'react';

export default function LoadingSpinner({ text = 'SYSTEM SYNCHRONIZING...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-[#263244]"></div>
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#FF6A00] animate-spin"></div>
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-t-[#00D4FF] animate-spin [animation-duration:1.5s]"></div>
      </div>
      <p className="text-xs uppercase font-mono tracking-widest text-[#8492A6] animate-pulse">
        {text}
      </p>
    </div>
  );
}

