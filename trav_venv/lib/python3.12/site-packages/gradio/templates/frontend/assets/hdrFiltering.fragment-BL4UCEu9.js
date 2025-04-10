import{j as e}from"./index-D5JzhMbY.js";import"./helperFunctions-DCFLaJMZ.js";import"./hdrFilteringFunctions-Bm40RDof.js";import"./index-DoYKQVZE.js";import"./svelte/svelte.js";const r="hdrFilteringPixelShader",i=`#include<helperFunctions>
#include<importanceSampling>
#include<pbrBRDFFunctions>
#include<hdrFilteringFunctions>
uniform alphaG: f32;var inputTextureSampler: sampler;var inputTexture: texture_cube<f32>;uniform vFilteringInfo: vec2f;uniform hdrScale: f32;varying direction: vec3f;@fragment
fn main(input: FragmentInputs)->FragmentOutputs {var color: vec3f=radiance(uniforms.alphaG,inputTexture,inputTextureSampler,input.direction,uniforms.vFilteringInfo);fragmentOutputs.color= vec4f(color*uniforms.hdrScale,1.0);}`;e.ShadersStoreWGSL[r]||(e.ShadersStoreWGSL[r]=i);const c={name:r,shader:i};export{c as hdrFilteringPixelShaderWGSL};
//# sourceMappingURL=hdrFiltering.fragment-BL4UCEu9.js.map
