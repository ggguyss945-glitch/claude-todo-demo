import { W, H } from '../../lib.js';
import { svgOf } from '../v2/pro.js';
import { sky, lightning, horizon } from './ep2_B_storm.js';
export default () => ({ w: W, h: H, svg: svgOf(sky() + lightning(), 10) });
