import { streetReset, wrap } from '../sets.js';
export default (arg) => ({ w: 1920, h: 1080, svg: wrap(streetReset({ t: 0.2, glitch: arg !== 'noglitch' ? undefined : false }).svg) });
