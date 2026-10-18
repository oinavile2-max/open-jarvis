#version 330
uniform sampler2D scene;
uniform vec2 resolution;
uniform float neon_strength;
uniform float cognition;
uniform float phase;
out vec4 fragColor;
float hash(float x){ return fract(sin(x*127.1+31.7)*43758.5453); }
vec2 turn(vec2 p,float a){return mat2(cos(a),-sin(a),sin(a),cos(a))*p;}
vec2 curve(vec2 a,vec2 b,vec2 c,float t){
    return mix(mix(a,b,t),mix(b,c,t),t);
}
// Tapered curved dendrite with a travelling activation packet.
vec3 fibre(vec2 p,vec2 a,vec2 b,vec2 c,float width,float seed,float delay){
    float distanceToFibre=10.;float along=0.;
    vec2 previous=a;
    for(int j=1;j<=6;j++){
        float t=float(j)/6.;vec2 next=curve(a,b,c,t);
        vec2 edge=next-previous;
        float u=clamp(dot(p-previous,edge)/max(dot(edge,edge),.000001),0.,1.);
        float d=length(p-mix(previous,next,u));
        if(d<distanceToFibre){distanceToFibre=d;along=(float(j-1)+u)/6.;}
        previous=next;
    }
    float radius=width*mix(1.,.25,along);
    float core=exp(-pow(distanceToFibre/max(radius,.0008),2.));
    float halo=exp(-pow(distanceToFibre/(radius*3.+.003),2.));
    float clock=mod(phase*(.72+hash(seed)*.25)+hash(seed+8.)*2.6,2.6);
    float packet=exp(-pow((along+delay-clock)*17.,2.));
    return vec3(.08,.32,.43)*(core*.58+halo*.12)
         +vec3(.40,1.25,1.70)*packet*(core*1.4+halo*.40);
}
vec3 organicNeurons(vec2 uv){
    vec2 p=(uv*2.-1.)*resolution/min(resolution.x,resolution.y)*1.48;
    vec3 light=vec3(0.);
    for(int i=0;i<6;i++){
        float id=float(i);float angle=id*2.39996;
        float z=sin(angle+phase*.09);
        vec2 centre=vec2(cos(angle+phase*.09)*(.32+.25*hash(id+4.)),
                         (hash(id+9.)-.5)*1.15);
        centre+=.025*vec2(sin(phase*.35+id),cos(phase*.28+id));
        vec2 local=turn(p-centre,id*1.7+phase*.035);
        if(length(local)>.55)continue;
        vec3 cell=vec3(0.);
        // Uneven branching silhouette around a small cell body.
        float polar=atan(local.y,local.x);
        float bodyRadius=.024*(1.+.18*sin(polar*5.+id)+.12*cos(polar*3.-id));
        float body=exp(-pow(length(local)/bodyRadius,2.));
        float fire=pow(max(0.,sin(phase*3.4+id*2.1)),14.);
        cell+=vec3(.18,.65,.84)*body*(.5+fire*1.8);
        for(int k=0;k<5;k++){
            float seed=id*41.+float(k)*7.;
            float direction=float(k)*1.2566+(hash(seed)-.5)*.72;
            float extent=.20+.20*hash(seed+1.);
            vec2 tip=turn(vec2(extent,0.),direction);
            vec2 bend=turn(vec2(extent*.48,(hash(seed+2.)-.5)*.20),direction);
            cell+=fibre(local,vec2(0.),bend,tip,.0038,seed,0.);
            // Daughter fibres grow out of the parent curve, with delayed pulses.
            for(int fork=0;fork<2;fork++){
                float split=.38+float(fork)*.25;
                vec2 root=curve(vec2(0.),bend,tip,split);
                float side=fork==0?-1.:1.;
                vec2 end=root+turn(vec2(extent*.44,0.),direction+side*(.48+hash(seed+3.)*.7));
                vec2 control=mix(root,end,.5)+turn(vec2(0.,.035*side),direction);
                cell+=fibre(local,root,control,end,.0022,seed,split);
            }
        }
        float depth=.38+.62*smoothstep(-1.,1.,z);
        light+=cell*depth;
    }
    return light*cognition*(1.-smoothstep(.83,1.16,length(p)));
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
    if(cognition>.003) colour+=organicNeurons(uv);
    // Slight colour separation preserves orange/magenta shadows and gold peaks.
    colour=vec3(1)-exp(-colour*(1.+neon_strength*.42));
    float alpha=max(base.a,max(colour.r,max(colour.g,colour.b)));
    fragColor=vec4(min(colour,vec3(alpha)),alpha);
}
