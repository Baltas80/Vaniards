#!/usr/bin/env python3
"""Add pointer-transparent mobile control visuals to the exported HTML5 build."""
from __future__ import annotations
import sys
from pathlib import Path

OVERLAY = r'''
<style id="vaniards-mobile-controls">
  #vaniards-mobile-controls {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 99999;
    user-select: none;
    -webkit-user-select: none;
  }
  #vaniards-mobile-controls .vc-joystick {
    position: absolute;
    left: 10%;
    bottom: 9%;
    width: 20%;
    aspect-ratio: 1;
    border-radius: 50%;
    box-sizing: border-box;
    border: 3px solid rgba(220,225,235,.38);
    background: radial-gradient(circle at 50% 50%, rgba(120,135,165,.20) 0 33%, rgba(30,35,50,.22) 34% 70%, rgba(10,12,18,.14) 71% 100%);
    box-shadow: inset 0 0 0 2px rgba(20,25,38,.20), 0 3px 9px rgba(0,0,0,.20);
  }
  #vaniards-mobile-controls .vc-knob {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 42%;
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: rgba(165,178,205,.38);
    border: 2px solid rgba(235,240,250,.42);
    box-shadow: 0 2px 6px rgba(0,0,0,.20);
  }
  #vaniards-mobile-controls .vc-button {
    position: absolute;
    width: 10.5%;
    aspect-ratio: 1;
    border-radius: 50%;
    display: grid;
    place-items: center;
    box-sizing: border-box;
    background: rgba(150,165,195,.28);
    border: 3px solid rgba(35,40,55,.48);
    box-shadow: inset 0 0 0 1px rgba(225,230,242,.38), 0 3px 8px rgba(0,0,0,.22);
    color: rgba(255,255,255,.88);
    font: 700 clamp(9px, 1.35vw, 20px)/1 sans-serif;
    letter-spacing: .03em;
    text-shadow: 1px 1px 2px rgba(0,0,0,.50);
  }
  #vaniards-mobile-controls .dash { right: 12%; bottom: 34%; }
  #vaniards-mobile-controls .jump { right: 29%; bottom: 9%; }
  #vaniards-mobile-controls .atk  { right: 6%;  bottom: 9%; }

  @media (orientation: portrait) {
    #vaniards-mobile-controls .vc-joystick { left: 6%; bottom: 8%; width: 25%; }
    #vaniards-mobile-controls .vc-button { width: 14%; }
    #vaniards-mobile-controls .dash { right: 10%; bottom: 31%; }
    #vaniards-mobile-controls .jump { right: 29%; bottom: 8%; }
    #vaniards-mobile-controls .atk  { right: 5%; bottom: 8%; }
  }
</style>
<div id="vaniards-mobile-controls" aria-hidden="true">
  <div class="vc-joystick"><div class="vc-knob"></div></div>
  <div class="vc-button dash">DASH</div>
  <div class="vc-button jump">JUMP</div>
  <div class="vc-button atk">ATK</div>
</div>
<script>
(function () {
  function mount() {
    var canvas = document.querySelector('canvas');
    var overlay = document.getElementById('vaniards-mobile-controls');
    if (!canvas || !overlay) { setTimeout(mount, 300); return; }
    var parent = canvas.parentElement;
    if (!parent) return;
    if (getComputedStyle(parent).position === 'static') parent.style.position = 'relative';
    parent.appendChild(overlay);
    overlay.style.width = canvas.clientWidth + 'px';
    overlay.style.height = canvas.clientHeight + 'px';
    overlay.style.left = canvas.offsetLeft + 'px';
    overlay.style.top = canvas.offsetTop + 'px';
    function resize() {
      overlay.style.width = canvas.clientWidth + 'px';
      overlay.style.height = canvas.clientHeight + 'px';
      overlay.style.left = canvas.offsetLeft + 'px';
      overlay.style.top = canvas.offsetTop + 'px';
    }
    window.addEventListener('resize', resize, {passive:true});
    new ResizeObserver(resize).observe(canvas);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
</script>
'''


def main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "vaniards-mobile-controls" in text:
        print("Mobile control overlay already present.")
        return
    marker = "</body>"
    if marker in text:
        text = text.replace(marker, OVERLAY + "\n" + marker, 1)
    else:
        text += "\n" + OVERLAY
    path.write_text(text, encoding="utf-8")
    print("Injected joystick-style mobile control overlay.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: inject_mobile_controls_overlay.py <index.html>")
    main(Path(sys.argv[1]))
