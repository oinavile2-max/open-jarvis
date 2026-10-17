#version 330
uniform vec2 resolution;
uniform float phase;
uniform float energy;
uniform float turbulence;
uniform float expansion;
uniform float intensity;
uniform int quality_steps;
out vec4 fragColor;

// Original procedural density field: advected wisps, ash and embedded embers.
// No image/video sampling. The volume is integrated front to back.
float hash3(vec3 p) {
    p = fract(p * .1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}
float noise3(vec3 p) {
    vec3 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
    return mix(mix(mix(hash3(i),hash3(i+vec3(1,0,0)),f.x),
                   mix(hash3(i+vec3(0,1,0)),hash3(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash3(i+vec3(0,0,1)),hash3(i+vec3(1,0,1)),f.x),
                   mix(hash3(i+vec3(0,1,1)),hash3(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float fbm(vec3 p) {
    float v=0., a=.55;
    mat3 rot=mat3(.00,.80,.60,-.80,.36,-.48,-.60,-.48,.64);
    for(int k=0;k<4;k++){v+=a*noise3(p);p=rot*p*2.13+7.31;a*=.49;}
    return v;
}
vec3 warp(vec3 p,float t) {
    vec3 q=vec3(fbm(p*1.7+vec3(0,t*.14,0)),
                fbm(p*1.7+vec3(5.3,0,-t*.12)),
                fbm(p*1.7+vec3(-t*.10,9.1,2.4)))-.5;
    return p+q*(.56+.28*turbulence);
}
void main(){
    vec2 uv=(2.*gl_FragCoord.xy-resolution)/min(resolution.x,resolution.y);
    uv*=1.48;
    if(dot(uv,uv)>2.08){fragColor=vec4(0);return;}
    vec3 ro=vec3(uv,2.0), rd=vec3(0,0,-1);
    float t=phase;
    float yaw=t*.115+.18*sin(t*.21), c=cos(yaw), s=sin(yaw);
    mat3 rot=mat3(c,0,s,0,1,0,-s,0,c);
    vec3 sum=vec3(0); float trans=1.;
    float stepSize=2.7/float(quality_steps);
    // Subpixel dither hides slice bands without frame-to-frame sparkle.
    float jitter=hash3(vec3(gl_FragCoord.xy,0));
    for(int k=0;k<96;k++){
        if(k>=quality_steps || trans<.012)break;
        float z=.62+(float(k)+jitter)*stepSize;
        vec3 p=rot*(ro+rd*z)/expansion;
        vec3 q=warp(p,t);
        float radial=length(q);
        float envelope=1.-smoothstep(.76,1.15,radial);
        if(envelope<.002)continue;
        vec3 flow=q*4.7+vec3(t*.12,-t*.29,t*.09);
        float billow=fbm(flow);
        float folds=abs(sin((billow*.74+noise3(flow*2.1)*.26)*37.+radial*7.));
        float fibre=pow(1.-folds,6.);
        float shell=exp(-pow((radial-.81)*5.,2.));
        float density=envelope*(.16+billow*.33+fibre*3.4*shell);
        float pockets=fbm(q*3.4+vec3(-t*.23,t*.11,4.1));
        float heat=smoothstep(.40,.72,pockets+.13*(1.-radial));
        heat*=.65+.35*intensity;
        float vein=pow(max(0.,1.-abs(billow-.49)*4.2),7.);
        vec3 ember=mix(vec3(.48,.003,.025),vec3(3.4,.26,.012),heat);
        ember=mix(ember,vec3(6.0,1.65,.20),pow(heat,5.));
        float inward=1.-smoothstep(.43,1.03,radial);
        vec3 emission=ember*(heat*.8+vein*.85)*(.06+inward*2.2)*(1.28+energy*.80);
        float light=clamp(.45+.5*q.y+.2*q.x,.1,1.);
        vec3 ash=mix(vec3(.10,.105,.12),vec3(.78,.77,.78),light);
        // Ash self-occlusion keeps hot pockets inside the smoke, not on a disc.
        vec3 source=ash*(.20+fibre*.95)*shell+emission;
        float alpha=1.-exp(-density*stepSize*3.3);
        sum+=trans*alpha*source;
        trans*=1.-alpha;
    }
    float alpha=1.-trans;
    vec3 colour=vec3(1)-exp(-sum*1.45);
    // Premultiplied alpha for native Qt compositing on any wallpaper.
    colour=pow(max(colour,vec3(0)),vec3(.80));
    fragColor=vec4(min(colour,vec3(alpha)),alpha);
}
