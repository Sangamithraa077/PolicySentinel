import { useEffect, type RefObject } from "react";

/** Calls `onOutside` for any pointerdown outside `ref`'s element — used to
 * close dropdown/popover menus like the Topbar's company switcher. */
export function useClickOutside(ref: RefObject<HTMLElement | null>, onOutside: () => void) {
  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        onOutside();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [ref, onOutside]);
}
