import React, { useState } from 'react';
import { BookOpen, Folder, FileText, ChevronRight, Copy, Check } from 'lucide-react';

export default function OneNoteBreadcrumb({ notebook, section, page }) {
  const [copied, setCopied] = useState(false);

  // Clean RoboFlow suffixes or raw filename formatting if present
  const formatTitle = (title) => {
    if (!title) return 'Page';
    const cleaned = String(title)
      .replace(/(_jpg|\.jpg|_jpeg|\.jpeg|_png|\.png)\.rf\.[a-f0-9]+/gi, '')
      .replace(/[-_]/g, ' ')
      .trim();
    return cleaned.split(' ')
      .map(w => w.toUpperCase() === w ? w : w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ') || title;
  };

  const cleanNb = notebook || 'Master Archive';
  const cleanSec = section || 'General';
  const cleanPg = formatTitle(page);
  const fullPath = `${cleanNb} > ${cleanSec} > ${cleanPg}`;

  const handleCopy = (e) => {
    e.stopPropagation();
    e.preventDefault();
    navigator.clipboard.writeText(fullPath);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="onenote-breadcrumb-container">
      <div className="onenote-breadcrumb" title={`Location: ${fullPath}`}>
        <div className="breadcrumb-part">
          <BookOpen size={13} style={{ color: '#c084fc', flexShrink: 0 }} />
          <span>{cleanNb}</span>
        </div>
        <ChevronRight size={11} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
        <div className="breadcrumb-part">
          <Folder size={13} style={{ color: '#d4af37', flexShrink: 0 }} />
          <span>{cleanSec}</span>
        </div>
        <ChevronRight size={11} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
        <div className="breadcrumb-part active">
          <FileText size={13} style={{ color: '#38bdf8', flexShrink: 0 }} />
          <span title={cleanPg}>{cleanPg}</span>
        </div>
      </div>
      <button 
        type="button"
        className="btn-copy-location"
        onClick={handleCopy}
        title="Copy exact OneNote hierarchy location"
      >
        {copied ? <Check size={11} style={{ color: '#10b981' }} /> : <Copy size={11} />}
        {copied && <span className="copy-feedback">Copied!</span>}
      </button>
    </div>
  );
}
