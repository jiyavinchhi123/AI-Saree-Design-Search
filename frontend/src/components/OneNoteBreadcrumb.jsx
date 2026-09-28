import React, { useState } from 'react';
import { BookOpen, Folder, FileText, ChevronRight, Copy, Check, Image as ImageIcon } from 'lucide-react';

export default function OneNoteBreadcrumb({ notebook, section, page, imageOrder }) {
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

  const cleanNb = notebook || 'My Notebook';
  const cleanSec = section || 'Section';
  const cleanPg = formatTitle(page);
  const orderStr = imageOrder ? `Image #${imageOrder}` : null;
  const fullPath = orderStr 
    ? `${cleanNb} > ${cleanSec} > ${cleanPg} > ${orderStr}`
    : `${cleanNb} > ${cleanSec} > ${cleanPg}`;

  const handleCopy = (e) => {
    e.stopPropagation();
    e.preventDefault();
    navigator.clipboard.writeText(fullPath);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: 'var(--bg-subtle)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '7px 10px',
      fontSize: '0.74rem',
      color: 'var(--text-secondary)',
      marginBottom: '10px',
      gap: '8px'
    }}>
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          flexWrap: 'wrap',
          minWidth: 0
        }}
        title={`Exact Location: ${fullPath}`}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 600, color: 'var(--primary-purple)' }}>
          <BookOpen size={13} style={{ color: 'var(--primary-purple)', flexShrink: 0 }} />
          <span>{cleanNb}</span>
        </span>
        <ChevronRight size={11} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 600, color: 'var(--gold-primary)' }}>
          <Folder size={13} style={{ color: 'var(--gold-primary)', flexShrink: 0 }} />
          <span>{cleanSec}</span>
        </span>
        <ChevronRight size={11} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 600, color: 'var(--text-main)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          <FileText size={13} style={{ color: '#2563eb', flexShrink: 0 }} />
          <span>{cleanPg}</span>
        </span>
        {orderStr && (
          <>
            <ChevronRight size={11} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: 'var(--gold-text)', background: 'var(--gold-light)', padding: '1px 6px', borderRadius: '4px' }}>
              <ImageIcon size={11} style={{ color: 'var(--gold-primary)', flexShrink: 0 }} />
              <span>{orderStr}</span>
            </span>
          </>
        )}
      </div>

      <button 
        type="button"
        onClick={handleCopy}
        title="Copy full OneNote location hierarchy"
        style={{
          background: copied ? 'var(--emerald-light)' : '#ffffff',
          border: '1px solid',
          borderColor: copied ? 'var(--emerald-border)' : 'var(--border-subtle)',
          borderRadius: '4px',
          padding: '3px 6px',
          color: copied ? 'var(--accent-emerald)' : 'var(--text-muted)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '0.68rem',
          fontWeight: 600,
          cursor: 'pointer',
          flexShrink: 0
        }}
      >
        {copied ? <Check size={11} /> : <Copy size={11} />}
        {copied && <span>Copied</span>}
      </button>
    </div>
  );
}
