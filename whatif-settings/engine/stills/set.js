// Still of one background set: arg = street | bedroom | kitchen | classroom | streetReset
import { SETS, wrap } from '../sets.js';
export default (arg = 'street') => {
  const set = SETS[arg](arg === 'streetReset' ? { t: 0.2 } : {});
  return { w: 1920, h: 1080, svg: wrap(set.svg) };
};
