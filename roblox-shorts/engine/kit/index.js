// Kit entry point shared by the sets kit (kitlib/props/suburb/sky/lighting/fx) and the character kit
// (util/faces/clothing/accessories/avatar/gnome/cast; API in README_CHARS.md).  import * as kit from '../kit/index.js'
export * from './kitlib.js';
export * from './props.js';
export * from './suburb.js';
export * from './sky.js';
export * from './lighting.js';
export * from './fx.js';
export * from './util.js';
export * from './faces.js';
export * from './clothing.js';
export * from './accessories.js';
export * from './avatar.js';
export * from './gnome.js';
export * from './cast.js';
// Names both kits export: explicit re-exports win over `export *` (otherwise they would be ambiguous and dropped).
export { STUD, shade, THREE } from './kitlib.js';
export { shade as shadeHex } from './util.js';
