// Tiny real WebGL draw plus browser capability queries. No engine internals.
const report={kind:'diagnostic_triangle',molecular_model_loaded:false,errors:[]};
try {
  const canvas=document.querySelector('canvas');
  const gl=canvas.getContext('webgl2',{preserveDrawingBuffer:true,antialias:false});
  if(!gl)throw new Error('WebGL2 unavailable');
  const shader=(type,source)=>{
    const object=gl.createShader(type);gl.shaderSource(object,source);gl.compileShader(object);
    if(!gl.getShaderParameter(object,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(object));
    return object;
  };
  const vertex=shader(gl.VERTEX_SHADER,`#version 300 es
in vec2 position; out vec2 uv;
void main(){uv=position;gl_Position=vec4(position,0,1);}`);
  const fragment=shader(gl.FRAGMENT_SHADER,`#version 300 es
precision highp float; in vec2 uv; out vec4 color;
void main(){color=vec4(.3+.3*uv.x,.5+.3*uv.y,.7,1);}`);
  const program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-.8,-.8,.8,-.8,0,.8]),gl.STATIC_DRAW);
  const attribute=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(attribute);
  gl.vertexAttribPointer(attribute,2,gl.FLOAT,false,0,0);gl.viewport(0,0,256,256);
  gl.clearColor(1,1,1,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,3);
  const pixels=new Uint8Array(256*256*4);gl.readPixels(0,0,256,256,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
  const colors=new Set();for(let i=0;i<pixels.length;i+=4*17)colors.add(`${pixels[i]},${pixels[i+1]},${pixels[i+2]}`);
  const debug=gl.getExtension('WEBGL_debug_renderer_info');
  report.graphics={webgl:true,version:gl.getParameter(gl.VERSION),renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),
    vendor:debug?gl.getParameter(debug.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR),sampled_colors:colors.size,error:gl.getError()};
  report.webgpu={secure_context:isSecureContext,api_exposed:!!navigator.gpu,adapter_available:false};
  if(navigator.gpu) {
    try {
      const adapter=await Promise.race([navigator.gpu.requestAdapter(),new Promise((_,reject)=>setTimeout(()=>reject(new Error('adapter timeout')),3000))]);
      report.webgpu.adapter_available=!!adapter;
      if(adapter?.info) {
        const info=adapter.info;report.webgpu.adapter={vendor:info.vendor,architecture:info.architecture,device:info.device,
          description:info.description,fallback:info.isFallbackAdapter};
      }
    } catch(error) {report.webgpu.error=String(error);}
  }
} catch(error) {report.errors.push(String(error));}
window.__sabuesoGraphicsDiagnostic=report;
document.documentElement.dataset.graphicsReady='true';
