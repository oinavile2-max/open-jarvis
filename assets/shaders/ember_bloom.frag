#version 330
uniform sampler2D scene;
uniform vec2 resolution;
uniform float neon_strength;
out vec4 fragColor;
void main(){
    vec2 uv=gl_FragCoord.xy/resolution;
    vec4 base=texture(scene,uv);
    vec3 glow=vec3(0);float weightSum=0.;
    // Soft emissive spill follows the actual hot volume, never a fixed ring.
    for(int y=-3;y<=3;y++)for(int x=-3;x<=3;x++){
        vec2 offset=vec2(x,y);
        float weight=exp(-dot(offset,offset)*.24);
        vec3 sampleColour=texture(scene,uv+offset*3.1/resolution).rgb;
        float hot=smoothstep(.38,.9,max(sampleColour.r,max(sampleColour.g,sampleColour.b)));
        glow+=sampleColour*hot*weight;weightSum+=weight;
    }
    glow=glow/weightSum*.46*neon_strength;
    vec3 colour=base.rgb+glow;
    // Slight colour separation preserves orange/magenta shadows and gold peaks.
    colour=vec3(1)-exp(-colour*(1.+neon_strength*.42));
    float alpha=max(base.a,max(colour.r,max(colour.g,colour.b)));
    fragColor=vec4(min(colour,vec3(alpha)),alpha);
}
