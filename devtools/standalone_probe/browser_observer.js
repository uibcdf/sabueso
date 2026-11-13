// Development-only browser diagnostics. No molecular protocol or scene state is changed.
(() => {
  if (window === window.top) {
    window.__sabuesoObservedFrame = null;
    addEventListener('message', event => {
      const frame = document.querySelector('[data-testid="molecular-frame"]');
      if (frame && event.source === frame.contentWindow && event.data?.kind === 'sabueso-probe-browser-observation') {
        window.__sabuesoObservedFrame = event.data.observation;
      }
    });
    return;
  }
  const errors = [];
  addEventListener('error', event => errors.push(String(event.error ?? event.message)));
  addEventListener('unhandledrejection', event => errors.push(String(event.reason)));
  let webgpu = null;
  let drawn = null;
  async function inspectGpu() {
    const result = {secure_context:isSecureContext, api_exposed:!!navigator.gpu, adapter_available:false};
    if (navigator.gpu) {
      try {
        const adapter = await Promise.race([navigator.gpu.requestAdapter(),
          new Promise((_,reject) => setTimeout(() => reject(new Error('adapter timeout')),3000))]);
        result.adapter_available = !!adapter;
        if (adapter?.info) {
          const info = adapter.info;
          result.adapter = {vendor:info.vendor,architecture:info.architecture,device:info.device,
            description:info.description,fallback:info.isFallbackAdapter};
        }
      } catch (error) {result.error=String(error);}
    }
    webgpu = result;
  }
  inspectGpu();
  setInterval(() => {
    const canvas = document.querySelector('canvas');
    if (!canvas) return;
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return;
    if (!drawn) {
      const debug = gl.getExtension('WEBGL_debug_renderer_info');
      const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
      gl.readPixels(0,0,gl.drawingBufferWidth,gl.drawingBufferHeight,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      const colors = new Set();
      for (let i=0;i<pixels.length;i+=4*17) colors.add(`${pixels[i]},${pixels[i+1]},${pixels[i+2]},${pixels[i+3]}`);
      if (colors.size < 3) return;
      drawn = {webgl:true,width:gl.drawingBufferWidth,height:gl.drawingBufferHeight,
        renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),
        version:gl.getParameter(gl.VERSION),sampled_colors:colors.size,error:gl.getError()};
    }
    const rect = canvas.getBoundingClientRect();
    parent.postMessage({kind:'sabueso-probe-browser-observation',observation:{
      graphics:drawn,
      canvas_rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},webgpu,errors,
      external_requests:performance.getEntriesByType('resource').map(x=>x.name)
        .filter(x=>/^https?:/.test(x) && new URL(x).hostname!=='127.0.0.1')
    }},'*');
  },1000);
})();
