#version 330
uniform sampler2D scene;
uniform vec2 resolution;
uniform float neon_strength;
uniform float cognition;
uniform float phase;
out vec4 fragColor;
vec3 neuron(float id){
    float longitude=id*2.399963;
    float y=1.-2.*((id+.5)/16.);
    float radius=sqrt(max(0.,1.-y*y));
    vec3 p=vec3(cos(longitude)*radius,y,sin(longitude)*radius)*(.61+.12*sin(id*4.7));
    p+=.045*vec3(sin(phase*.8+id),cos(phase*.6+id*1.3),sin(phase*.4-id));
    float angle=phase*.115+.18*sin(phase*.21);
    return mat3(cos(angle),0,sin(angle),0,1,0,-sin(angle),0,cos(angle))*p;
}
vec3 synapses(vec2 uv){
    vec3 light=vec3(0);
    vec2 aspect=resolution/min(resolution.x,resolution.y);
    vec2 p=(uv*2.-1.)*aspect*1.48;
    for(int i=0;i<24;i++){
        float start=float(i%16);
        float finish=mod(start+(i<16?3.:7.),16.);
        vec3 a=neuron(start),b=neuron(finish);
        vec2 ab=b.xy-a.xy;
        float u=clamp(dot(p-a.xy,ab)/max(dot(ab,ab),.001),0.,1.);
        float dist=length(p-mix(a.xy,b.xy,u));
        float impulse=fract(phase*(1.8+.05*float(i%5))-float(i)*.173);
        float packet=exp(-pow((u-impulse)*20.,2.));
        float depth=mix(a.z,b.z,u);
        float front=.38+.62*smoothstep(-.6,.5,depth);
        float wire=exp(-dist*dist/0.00005);
        float aura=exp(-dist*dist/0.0009);
        vec3 tint=mix(vec3(.035,1.1,2.8),vec3(1.8,.15,.8),float(i%3)/2.);
        light+=tint*front*(wire*(.14+packet*1.8)+aura*packet*.40);
        float node=exp(-dot(p-a.xy,p-a.xy)/.00020);
        float arrival=exp(-pow(impulse*9.,2.));
        light+=tint*node*(.25+.8*arrival)*front;
    }
    return light*cognition;
}
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
    if(cognition>.005){
        vec3 signals=synapses(uv);
        float mask=clamp(max(signals.r,max(signals.g,signals.b))*.72,0.,.88);
        colour=mix(colour,signals,mask);
    }
    // Slight colour separation preserves orange/magenta shadows and gold peaks.
    colour=vec3(1)-exp(-colour*(1.+neon_strength*.42));
    float alpha=max(base.a,max(colour.r,max(colour.g,colour.b)));
    fragColor=vec4(min(colour,vec3(alpha)),alpha);
}
