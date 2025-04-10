import{j as r}from"./index-D5JzhMbY.js";import"./helperFunctions-CSS_2DGJ.js";import"./index-DoYKQVZE.js";import"./svelte/svelte.js";const e="rgbdEncodePixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#include<helperFunctions>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=toRGBD(texture2D(textureSampler,vUV).rgb);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const n={name:e,shader:o};export{n as rgbdEncodePixelShader};
//# sourceMappingURL=rgbdEncode.fragment-CQbH_Qou.js.map
