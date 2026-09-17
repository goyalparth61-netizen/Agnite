import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const children=[];
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const child of children)child.kill();process.exitCode=code;}
const processes=[
 ['server/start.mjs',['--env-file-if-exists=.env']],
 ['node_modules/vite/bin/vite.js',process.argv.slice(2)],
];
for(const [script,nodeArgs] of processes){
 const args=script==='server/start.mjs'?[...nodeArgs,script]:[script,...nodeArgs];
 const child=spawn(process.execPath,args,{cwd:root,stdio:'inherit',windowsHide:true});
 children.push(child);
 child.on('error',error=>{console.error(error.message);stop(1);});
 child.on('exit',code=>{if(!stopping)stop(code??1);});
}
process.on('SIGINT',()=>stop());
process.on('SIGTERM',()=>stop());
