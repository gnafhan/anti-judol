'use client';

/**
 * KeyboardShortcutsHelp Component - Auto ML Retraining
 * 
 * Displays available keyboard shortcuts for validation actions.
 * Shows as a tooltip/popover when triggered.
 * 
 * Requirements: 8.1, 8.3 - Keyboard shortcuts and help tooltip
 */

import { useState, useCallback, useEffect, useImperativeHandle, forwardRef } from 'react';
import { MdKeyboard, MdClose } from 'react-icons/md';

export interface KeyboardShortcut {
  /** Key or key combination */
  key: string;
  /** Description of the action */
  description: string;
  /** Category for grouping */
  category?: 'navigation' | 'validation' | 'general';
}

export interface KeyboardShortcutsHelpProps {
  /** Additional shortcuts to display */
  additionalShortcuts?: KeyboardShortcut[];
  /** Whether to show as compact badge */
  compact?: boolean;
  /** Custom class name */
  className?: string;
  /** Controlled open state */
  isOpen?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (isOpen: boolean) => void;
}

export interface KeyboardShortcutsHelpRef {
  /** Toggle the help panel */
  toggle: () => void;
  /** Open the help panel */
  open: () => void;
  /** Close the help panel */
  close: () => void;
}

/**
 * Default keyboard shortcuts for scan results
 */
const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  { key: '↑ / k', description: 'Previous comment', category: 'navigation' },
  { key: '↓ / j', description: 'Next comment', category: 'navigation' },
  { key: 'Home', description: 'First comment', category: 'navigation' },
  { key: 'End', description: 'Last comment', category: 'navigation' },
  { key: 'Esc', description: 'Clear selection', category: 'navigation' },
  // Validation
  { key: 'V', description: 'Validate as correct', category: 'validation' },
  { key: 'X', description: 'Mark as incorrect', category: 'validation' },
  { key: 'Enter', description: 'Confirm action', category: 'validation' },
  { key: 'G', description: 'Correct to Gambling', category: 'validation' },
  { key: 'C', description: 'Correct to Clean', category: 'validation' },
];

/**
 * Keyboard key badge component
 */
const KeyBadge = ({ children }: { children: React.ReactNode }) => (
  <kbd className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 text-xs font-mono font-medium bg-gray-100 dark:bg-navy-600 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-navy-500 rounded shadow-sm">
    {children}
  </kbd>
);

/**
 * KeyboardShortcutsHelp - Displays keyboard shortcuts help
 * 
 * @example
 * ```tsx
 * // Uncontrolled usage
 * <KeyboardShortcutsHelp />
 * 
 * // Controlled usage with ref
 * const helpRef = useRef<KeyboardShortcutsHelpRef>(null);
 * <KeyboardShortcutsHelp ref={helpRef} />
 * // Then call helpRef.current?.toggle() from keyboard handler
 * ```
 */
const KeyboardShortcutsHelp = forwardRef<KeyboardShortcutsHelpRef, KeyboardShortcutsHelpProps>(({
  additionalShortcuts = [],
  compact = false,
  className = '',
  isOpen: controlledIsOpen,
  onOpenChange,
}, ref) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  
  // Support both controlled and uncontrolled modes
  const isControlled = controlledIsOpen !== undefined;
  const isOpen = isControlled ? controlledIsOpen : internalIsOpen;

  const allShortcuts = [...DEFAULT_SHORTCUTS, ...additionalShortcuts];
  
  const navigationShortcuts = allShortcuts.filter(s => s.category === 'navigation');
  const validationShortcuts = allShortcuts.filter(s => s.category === 'validation');
  const generalShortcuts = allShortcuts.filter(s => s.category === 'general' || !s.category);

  const setIsOpen = useCallback((value: boolean) => {
    if (!isControlled) {
      setInternalIsOpen(value);
    }
    onOpenChange?.(value);
  }, [isControlled, onOpenChange]);

  const toggleOpen = useCallback(() => {
    setIsOpen(!isOpen);
  }, [isOpen, setIsOpen]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, [setIsOpen]);

  const handleOpen = useCallback(() => {
    setIsOpen(true);
  }, [setIsOpen]);

  // Expose methods via ref for external control
  useImperativeHandle(ref, () => ({
    toggle: toggleOpen,
    open: handleOpen,
    close: handleClose,
  }), [toggleOpen, handleOpen, handleClose]);

  // Listen for ? key to toggle help (global shortcut)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle if user is typing in an input
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      if (event.key === '?') {
        event.preventDefault();
        toggleOpen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleOpen]);

  return (
    <div className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        onClick={toggleOpen}
        className={`inline-flex items-center gap-1.5 transition-colors ${
          compact
            ? 'p-1.5 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-700'
            : 'px-3 py-1.5 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-gray-100 dark:bg-navy-700 hover:bg-gray-200 dark:hover:bg-navy-600'
        }`}
        title="Keyboard shortcuts"
        aria-label="Show keyboard shortcuts"
        aria-expanded={isOpen}
      >
        <MdKeyboard className={compact ? 'h-4 w-4' : 'h-5 w-5'} />
        {!compact && <span>Shortcuts</span>}
      </button>

      {/* Shortcuts Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={handleClose}
            aria-hidden="true"
          />
          
          {/* Panel */}
          <div 
            className="absolute right-0 top-full mt-2 z-50 w-72 bg-white dark:bg-navy-800 rounded-xl shadow-xl border border-gray-200 dark:border-navy-600 overflow-hidden"
            role="dialog"
            aria-label="Keyboard shortcuts"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-navy-700 border-b border-gray-200 dark:border-navy-600">
              <h3 className="text-sm font-semibold text-navy-700 dark:text-white flex items-center gap-2">
                <MdKeyboard className="h-4 w-4" />
                Keyboard Shortcuts
              </h3>
              <button
                onClick={handleClose}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
                aria-label="Close"
              >
                <MdClose className="h-4 w-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 space-y-4 max-h-80 overflow-y-auto">
              {/* Navigation Section */}
              {navigationShortcuts.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                    Navigation
                  </h4>
                  <div className="space-y-2">
                    {navigationShortcuts.map((shortcut, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {shortcut.description}
                        </span>
                        <KeyBadge>{shortcut.key}</KeyBadge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Validation Section */}
              {validationShortcuts.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                    Validation
                  </h4>
                  <div className="space-y-2">
                    {validationShortcuts.map((shortcut, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {shortcut.description}
                        </span>
                        <KeyBadge>{shortcut.key}</KeyBadge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* General Section */}
              {generalShortcuts.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                    General
                  </h4>
                  <div className="space-y-2">
                    {generalShortcuts.map((shortcut, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {shortcut.description}
                        </span>
                        <KeyBadge>{shortcut.key}</KeyBadge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer hint */}
            <div className="px-4 py-2 bg-gray-50 dark:bg-navy-700 border-t border-gray-200 dark:border-navy-600">
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                Press <KeyBadge>?</KeyBadge> to toggle this help
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
});

KeyboardShortcutsHelp.displayName = 'KeyboardShortcutsHelp';

export default KeyboardShortcutsHelp;
