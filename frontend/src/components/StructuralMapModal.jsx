import React from 'react';
import { X, ShieldCheck, Cpu } from 'lucide-react';

export default function StructuralMapModal({ isOpen, onClose, originalUrl, structuralUrl, title }) {
  if (!isOpen) return null;

  return (
    <div 
      className="modal-backdrop" 
      onClick={onClose} 
      id="structural-modal"
      role="dialog"
      aria-modal="true"
    >
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '22px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--purple-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary-purple)'
            }}>
              <Cpu size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', color: 'var(--text-main)', margin: 0 }}>AI Vision Structural Map</h3>
              <p style={{ fontSize: '0.80rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                {title || 'Color-Invariant Motif & Edge Inspection'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            id="btn-close-modal"
            aria-label="Close Modal"
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              cursor: 'pointer'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Dual View Side-by-side */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', 
          gap: '20px', 
          marginBottom: '24px' 
        }}>
          <div>
            <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Original Fabric (Colorway)
            </div>
            <div style={{ 
              borderRadius: 'var(--radius-lg)', 
              overflow: 'hidden', 
              border: '1px solid var(--border-subtle)', 
              aspectRatio: '1', 
              background: '#f8fafc',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <img src={originalUrl} alt="Original Fabric" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--primary-purple)', marginBottom: '8px' }}>
              AI Structural Map (Color Discarded)
            </div>
            <div style={{ 
              borderRadius: 'var(--radius-lg)', 
              overflow: 'hidden', 
              border: '2px solid var(--primary-purple)', 
              aspectRatio: '1', 
              background: '#090a0f', 
              boxShadow: 'var(--shadow-purple)'
            }}>
              <img src={structuralUrl} alt="Structural Map" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
          </div>
        </div>

        {/* Explanation Card */}
        <div style={{ 
          background: 'linear-gradient(135deg, var(--purple-light) 0%, var(--gold-light) 100%)', 
          border: '1px solid var(--purple-border)', 
          borderRadius: 'var(--radius-lg)', 
          padding: '18px' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--primary-purple)', fontWeight: 700, fontSize: '0.9rem' }}>
            <ShieldCheck size={18} /> How Color-Invariant Matching Works
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.55' }}>
            The AI Saree Design Engine eliminates chromatic channels (Hue &amp; Saturation) and decomposes the image into a 3-channel structural tensor comprising CLAHE contrast-normalized luminance, Sobel gradient edge magnitudes (for motif contours and temple spires), and adaptive texture channels (for jacquard weave patterns). This representation is processed through Meta's DINOv2 Self-Supervised Vision Transformer with 4-zone spatial motif pooling (Top Border, Body Field Jaal/Motifs, Bottom Border &amp; Pallu), allowing the exact same design in completely different colorways (e.g., Pink vs. Peacock Blue) to match with &gt;95% similarity while cleanly rejecting unrelated motifs.
          </p>
        </div>
      </div>
    </div>
  );
}
