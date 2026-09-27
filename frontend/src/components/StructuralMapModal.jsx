import React from 'react';
import { X, Eye, ShieldCheck, Cpu } from 'lucide-react';

export default function StructuralMapModal({ isOpen, onClose, originalUrl, structuralUrl, title }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} id="structural-modal">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu size={22} style={{ color: 'var(--gold-primary)' }} />
            <div>
              <h3>AI Vision Structural Map</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                {title || 'Color-Invariant Pattern Inspection'}
              </p>
            </div>
          </div>
          <button className="close-btn" onClick={onClose} id="btn-close-modal">
            <X size={20} />
          </button>
        </div>

        {/* Dual View Side-by-side */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              Original Fabric (Colorway)
            </div>
            <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)', aspectRatio: '1', background: '#000' }}>
              <img src={originalUrl} alt="Original Fabric" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--gold-light)', marginBottom: '8px' }}>
              AI Structural Map (Color Discarded)
            </div>
            <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1.5px solid var(--gold-primary)', aspectRatio: '1', background: '#000', boxShadow: 'var(--shadow-gold)' }}>
              <img src={structuralUrl} alt="Structural Map" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
          </div>
        </div>

        {/* Explanation Card */}
        <div style={{ background: 'rgba(212, 175, 55, 0.06)', border: '1px solid var(--border-active)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--gold-light)', fontWeight: 600, fontSize: '0.9rem' }}>
            <ShieldCheck size={18} /> How Color-Invariant Matching Works
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            The AI Saree Design Engine eliminates chromatic channels (Hue &amp; Saturation) and decomposes the image into a 3-channel structural tensor comprising CLAHE contrast-normalized luminance, Sobel gradient edge magnitudes (for motif contours and temple spires), and adaptive texture channels (for jacquard weave patterns). This representation is processed through Meta's DINOv2 Self-Supervised Vision Transformer with 4-zone spatial motif pooling (Top Border, Body Field Jaal/Motifs, Bottom Border &amp; Pallu), allowing the exact same design in completely different colorways (e.g., Pink vs. Peacock Blue) to match with &gt;95% similarity while cleanly rejecting unrelated motifs!
          </p>
        </div>
      </div>
    </div>
  );
}
