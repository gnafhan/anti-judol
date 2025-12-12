'use client';

/**
 * useKeyboardNavigation Hook - Auto ML Retraining
 * 
 * Provides keyboard navigation functionality for scan results.
 * Implements arrow key navigation between comments with focus management.
 * 
 * Requirements: 8.2 - Arrow key navigation between comments
 */

import { useState, useCallback, useEffect, useRef } from 'react';

export interface UseKeyboardNavigationOptions {
  /** Total number of items to navigate */
  itemCount: number;
  /** Whether keyboard navigation is enabled */
  enabled?: boolean;
  /** Callback when focused item changes */
  onFocusChange?: (index: number) => void;
  /** Callback when Enter is pressed on focused item */
  onSelect?: (index: number) => void;
  /** Container element ref for scroll management */
  containerRef?: React.RefObject<HTMLElement>;
}

export interface UseKeyboardNavigationReturn {
  /** Currently focused item index (-1 if none) */
  focusedIndex: number;
  /** Set the focused index manually */
  setFocusedIndex: (index: number) => void;
  /** Check if an item is focused */
  isFocused: (index: number) => boolean;
  /** Get props to spread on navigable items */
  getItemProps: (index: number) => {
    tabIndex: number;
    'data-focused': boolean;
    'aria-selected': boolean;
    ref: (el: HTMLElement | null) => void;
  };
  /** Reset focus to none */
  resetFocus: () => void;
  /** Move focus to next item */
  focusNext: () => void;
  /** Move focus to previous item */
  focusPrevious: () => void;
}

/**
 * Custom hook for keyboard navigation in lists
 * 
 * @example
 * ```tsx
 * const { focusedIndex, getItemProps } = useKeyboardNavigation({
 *   itemCount: items.length,
 *   onSelect: (index) => handleSelect(items[index]),
 * });
 * 
 * return items.map((item, index) => (
 *   <div key={item.id} {...getItemProps(index)}>
 *     {item.content}
 *   </div>
 * ));
 * ```
 */
export function useKeyboardNavigation({
  itemCount,
  enabled = true,
  onFocusChange,
  onSelect,
  containerRef,
}: UseKeyboardNavigationOptions): UseKeyboardNavigationReturn {
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const itemRefs = useRef<Map<number, HTMLElement>>(new Map());

  /**
   * Scroll focused item into view
   */
  const scrollIntoView = useCallback((index: number) => {
    const element = itemRefs.current.get(index);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, []);

  /**
   * Move focus to next item
   */
  const focusNext = useCallback(() => {
    if (itemCount === 0) return;
    
    setFocusedIndex((prev) => {
      const next = prev < itemCount - 1 ? prev + 1 : 0;
      scrollIntoView(next);
      onFocusChange?.(next);
      return next;
    });
  }, [itemCount, scrollIntoView, onFocusChange]);

  /**
   * Move focus to previous item
   */
  const focusPrevious = useCallback(() => {
    if (itemCount === 0) return;
    
    setFocusedIndex((prev) => {
      const next = prev > 0 ? prev - 1 : itemCount - 1;
      scrollIntoView(next);
      onFocusChange?.(next);
      return next;
    });
  }, [itemCount, scrollIntoView, onFocusChange]);

  /**
   * Reset focus
   */
  const resetFocus = useCallback(() => {
    setFocusedIndex(-1);
  }, []);

  /**
   * Handle keyboard events
   */
  useEffect(() => {
    if (!enabled) return;

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

      switch (event.key) {
        case 'ArrowDown':
        case 'j': // Vim-style navigation
          event.preventDefault();
          focusNext();
          break;
        case 'ArrowUp':
        case 'k': // Vim-style navigation
          event.preventDefault();
          focusPrevious();
          break;
        case 'Enter':
          if (focusedIndex >= 0) {
            event.preventDefault();
            onSelect?.(focusedIndex);
          }
          break;
        case 'Escape':
          event.preventDefault();
          resetFocus();
          break;
        case 'Home':
          event.preventDefault();
          setFocusedIndex(0);
          scrollIntoView(0);
          onFocusChange?.(0);
          break;
        case 'End':
          event.preventDefault();
          const lastIndex = itemCount - 1;
          setFocusedIndex(lastIndex);
          scrollIntoView(lastIndex);
          onFocusChange?.(lastIndex);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled, focusedIndex, focusNext, focusPrevious, resetFocus, onSelect, itemCount, scrollIntoView, onFocusChange]);

  /**
   * Check if an item is focused
   */
  const isFocused = useCallback(
    (index: number) => focusedIndex === index,
    [focusedIndex]
  );

  /**
   * Get props for navigable items
   */
  const getItemProps = useCallback(
    (index: number) => ({
      tabIndex: focusedIndex === index ? 0 : -1,
      'data-focused': focusedIndex === index,
      'aria-selected': focusedIndex === index,
      ref: (el: HTMLElement | null) => {
        if (el) {
          itemRefs.current.set(index, el);
        } else {
          itemRefs.current.delete(index);
        }
      },
    }),
    [focusedIndex]
  );

  // Reset focus when item count changes
  useEffect(() => {
    if (focusedIndex >= itemCount) {
      setFocusedIndex(itemCount > 0 ? itemCount - 1 : -1);
    }
  }, [itemCount, focusedIndex]);

  return {
    focusedIndex,
    setFocusedIndex,
    isFocused,
    getItemProps,
    resetFocus,
    focusNext,
    focusPrevious,
  };
}

export default useKeyboardNavigation;
