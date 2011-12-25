
/*
 * moochart
 *
 * @version		0.1b1
 * @license		MIT-style license
 * @author		Johan Nordberg <norddan@gmail.com>
 * @infos		http://moochart.coneri.se
 * @copyright	Author
 *
*/

var Chart = new Class({
	
	Version: '0.1b1',
	
	Implements: Options
	
});

Chart.Bubble = new Class({
	
	Extends: Chart,
	
	options: {
		width: 600,
		height: 400,
		xmin: 0, xmax: 100,
		ymin: 0, ymax: 100,
		zmin: 0, zmax: 1,
		xsteps: 5,
		ysteps: 5,
		xlabel: null,
		ylabel: null,
		bubbleSize: 30,
		lineColor: '#000'
	},
	
	initialize: function(container, options) {
		
		this.setOptions(options);
		
		this.options.xsteps--;
		this.options.xsteps = this.options.xsteps.limit(1,50),
		
		this.options.ysteps--;
		this.options.ysteps = this.options.ysteps.limit(1,50),
		
		this.container = $(container);
		
		this.container.setStyles({
			'width': this.options.width,
			'height': this.options.height,
		});
		
		this.canvas = new Element('canvas');
		this.canvas.adopt(new Element('div', {
			'text': 'Your browser does not support the canvas element, get a better one!',
			'styles': {
				'text-align': 'center',
				'background-color': '#8b2e19',
				'width': this.options.width,
				'height': this.options.height,
				'color': '#fff'
			}
		}));
		this.canvas.width = this.options.width;
		this.canvas.height = this.options.height;
		this.container.adopt(this.canvas);
		
		if (!this.canvas.getContext) return false;
		
		this.overlay = new Element('div', {
			styles: {
				'position': 'relative',
				'width': this.options.width,
				'height': this.options.height,
				'top': 0-this.options.height-3,
				'margin-bottom': 0-this.options.height-3,
				'font-family': 'Helvetica, Arial, sans-serif',
				'z-index': 240
			}
		});
		this.overlay.addEvent('mousemove', this.mouseHandler.bind(this));
		this.overlay.addEvent('mouseout', function() {
			this.tip.style.display = 'none';
			this.activeBubble = -1;
			this.redraw();
		}.bind(this));
		this.container.adopt(this.overlay);
		
		this.tip = new Element('div', {
			text: '',
			styles: {
				'position': 'absolute',
				'display': 'none',
				'border': '2px solid #000',
				'background-color': '#262626',
				'padding': '0.5em',
				'-webkit-border-radius': '3px',
				'-moz-border-radius': '3px',
				'white-space': 'nowrap',
				'z-index': 250,
				'color': '#fff',
				'font-size': '11px',
				'line-height': '1.3em',
				'text-align': 'left'
			}
		});
		this.overlay.adopt(this.tip);
		
		this.ctx = this.canvas.getContext('2d');
		
		this.bubbles = new Array;
		this.activeBubble = -1;
		
		this.paddingTop = 30;
		this.paddingLeft = 40;
		this.paddingBottom = 30;
		this.paddingRight = 40;
		
		if (this.options.ylabel) this.paddingLeft+=30;
		if (this.options.xlabel) this.paddingBottom+=20;
		
		this.xwork = (this.options.width - (this.paddingLeft + this.paddingRight)) - this.options.bubbleSize * 2;
		this.ywork = (this.options.height - (this.paddingTop + this.paddingBottom)) - this.options.bubbleSize * 2;
		
		this.xmax = this.options.xmax;
		this.xmin = this.options.xmin;
		
		this.ymax = this.options.ymax;
		this.ymin = this.options.ymin;
		
		this.zmax = this.options.zmax;
		this.zmin = this.options.zmin;
		
		this.xnumbers = new Array;
		this.ynumbers = new Array;
		
		var xstep = this.xwork / this.options.xsteps;
		var ystep = this.ywork / this.options.ysteps;
		
		(this.options.xsteps + 1).times(function(i) {
			this.xnumbers.push(new Element('div', {
				text: '',
				styles: {
					'position': 'absolute',
					'font-size': '10px',
					'line-height': '20px',
					'height': '20px',
					'width': xstep + 'px',
					'text-align': 'center',
					'top': (this.options.height - this.paddingBottom + 10) + 'px',
					'left': (this.paddingLeft + this.options.bubbleSize) - (xstep / 2) + i * xstep + 'px',
					'color': this.options.lineColor
				}
			}));
		}.bind(this));

		(this.options.ysteps + 1).times(function(i) {
			this.ynumbers.push(new Element('div', {
				text: '',
				styles: {
					'position': 'absolute',
					'font-size': '10px',
					'line-height': '20px',
					'height': '20px',
					'vertical-align': 'middle',
					'width': (this.paddingLeft - 15) + 'px',
					'text-align': 'right',
					'top': (this.options.bubbleSize + (i * ystep) + this.paddingTop - 10) + 'px',
					'left': '0px',
					'color': this.options.lineColor
				}
			}));
		}.bind(this));

		this.overlay.adopt(this.xnumbers);
		this.overlay.adopt(this.ynumbers);
		
		var labelStyles = {
			'position': 'absolute',
			'font-size': '10px',
			'line-height': '20px',
			'width': (this.xwork) + 'px',
			'text-align': 'center',
			'bottom': '0px',
			'letter-spacing': '0.1em',
			'left': (this.paddingLeft + this.options.bubbleSize ) + 'px',
			'color': this.options.lineColor
		}
		
		if (this.options.xlabel) {
			
			this.xlabel = new Element('div', {
				text: this.options.xlabel,
				styles: labelStyles
			});
			
			this.overlay.adopt(this.xlabel, this.ylabel);
			
		}
		
		if (this.options.ylabel) {
			
			var ylabelText = '';
			var yl = this.options.ylabel;
			
			for(var i = 0; i < yl.length; i++) {
				ylabelText += "<br />" + yl.charAt(i);
			}
			
			this.ylabel = new Element('div', {
				html: ylabelText,
				styles: labelStyles
			});
			
			this.ylabel.setStyles({
				'width': '20px',
				'height': 1.1 * (i+2) + 'em',
				'left': '0px',
				'top': '0px',
				'line-height': '1.1em'
			});
			
			this.overlay.adopt(this.ylabel);
		
			var ylh = this.ylabel.getSize().y;
			this.ylabel.setStyle('top', (this.paddingTop + this.options.bubbleSize) + ((this.ywork - ylh) / 2));
		
		}
		
		this.drawLabels();
		this.updateNumbers();
		this.redraw();
	},
	
	drawLabels: function() {
		this.ctx.lineWidth = 4;
		this.ctx.lineCap = 'round';
	  	this.ctx.strokeStyle = this.options.lineColor;
	  	this.ctx.beginPath();
	  	this.ctx.moveTo(this.paddingLeft, this.paddingTop);
		this.ctx.lineTo(this.paddingLeft, this.options.height - this.paddingBottom);
		this.ctx.lineTo(this.options.width - this.paddingRight, this.options.height - this.paddingBottom);
	  	this.ctx.stroke();
		
		var xstep = this.xwork / this.options.xsteps;
		var ystep = this.ywork / this.options.ysteps;
		
	  	this.ctx.beginPath();
		this.ctx.lineWidth = 2;
		
		(this.options.xsteps + 1).times(function(i) {
			var mov = this.paddingLeft + this.options.bubbleSize + xstep * i;
	  		this.ctx.moveTo(mov, this.options.height - this.paddingBottom);
			this.ctx.lineTo(mov, this.options.height - this.paddingBottom + 10);
		}.bind(this));

		(this.options.ysteps + 1).times(function(i) {
			var mov = this.options.height - (this.paddingBottom + this.options.bubbleSize + ystep * i);
		  	this.ctx.moveTo(this.paddingLeft, mov);
			this.ctx.lineTo(this.paddingLeft - 10, mov);
		}.bind(this));
		
	  	this.ctx.stroke();
	
	},
	
	// color can be #fff, rgb(123,13,2) or array - [121,312,34]
	addBubble: function(x, y, z, color, tip) {
		
		if ($type(color) == 'array') color = 'rgb('+color.join(',')+')';
		
		x = parseInt(x);
		y = parseInt(y);
		z = parseInt(z);
		
		tip = tip.replace(/%x/ig, x);
		tip = tip.replace(/%y/ig, y);
		tip = tip.replace(/%z/ig, z);
		
		this.bubbles.push({
			x: x,
			y: y,
			z: z,
			color: color,
			tip: tip
		});
				
		if (z > this.zmax) this.zmax = z;
		if (z < this.zmin) this.zmin = z;
		
		if (x > this.xmax) this.xmax = x;
		if (x < this.xmin) this.xmin = x;
		
		if (y > this.ymax) this.ymax = y;
		if (y < this.ymin) this.ymin = y;
		
		this.updateNumbers();
		
		// Big goes to the back!
		this.bubbles.sort(function(a, b) { return b.z - a.z; });
	},
	
	updateNumbers: function() {
		
		var xstep = (this.xmax - this.xmin) / this.options.xsteps;
		this.xnumbers.each(function(el, i) { el.set('text', (xstep * i + this.xmin).round()); }.bind(this));
		
		var ystep = (this.ymax - this.ymin) / this.options.ysteps;
		this.ynumbers.each(function(el, i) { el.set('text', (this.ymax + this.ymin) - ((ystep*i) + this.ymin).round()); }.bind(this));
	
	},
	
	mouseHandler: function(e) {
		
		var pos = this.canvas.getCoordinates();
		var x = e.page.x - pos.left, y = e.page.y - pos.top;
		var active = -1, l = this.bubbles.length;
		
   // this.ctx.fillStyle = '#000';
   // this.ctx.beginPath();
   // this.ctx.arc(x, y, 2, 0, Math.PI * 2, true);
   // this.ctx.fill();
		
		for (var i = l - 1; i >= 0; i--) {
			var cx = x - this.bubbles[i].realx, cy = y - this.bubbles[i].realy, cz = this.bubbles[i].realz + 1;
			if ((cx * cx) + (cy * cy) <= (cz * cz)) {
				active = i;
				break;
			}
		}
		
		if (this.activeBubble != active) {
			this.activeBubble = active;
			this.redraw();
			if (this.activeBubble >= 0) {
				this.tip.set('html', this.bubbles[this.activeBubble].tip);
				this.tip.setStyle('display', 'block');
			} else {
				this.tip.setStyle('display', 'none');
			}
		}
		
		if (this.activeBubble >= 0) {
			this.tip.setStyle('left', x + 10);
			this.tip.setStyle('top', y + 15);
		}
		
		
	},
	
	redraw: function() {
		var l = this.bubbles.length;
		this.ctx.clearRect(this.paddingLeft + 2, 0, this.options.width, this.options.height - (this.paddingBottom + 2));
		this.ctx.lineWidth = 1;
		for(var i = 0; i < l; i++) {
			var x = (((this.bubbles[i].x - this.xmin) / (this.xmax - this.xmin)) * this.xwork).round() + this.paddingLeft + this.options.bubbleSize;
			var y = (this.ywork - (((this.bubbles[i].y - this.ymin) / (this.ymax - this.ymin)) * this.ywork).round()) + this.paddingTop + this.options.bubbleSize;
			var z = (((this.bubbles[i].z - this.zmin) / (this.zmax - this.zmin)) * (this.options.bubbleSize - 8)).round() + 5;

			this.ctx.beginPath();
			this.ctx.globalAlpha = 1;
			this.ctx.fillStyle = this.bubbles[i].color;
			this.ctx.strokeStyle = this.bubbles[i].color;
			this.ctx.arc(x, y, z, 0, Math.PI * 2, true);
			this.ctx.stroke();
			if (this.activeBubble != i) this.ctx.globalAlpha = 0.6;
			this.ctx.fill();
			
			this.bubbles[i].realx = x; this.bubbles[i].realy = y; this.bubbles[i].realz = z;
		}
	},
	
	clear: function() {
    	this.ctx.clearRect(0, 0, this.options.width, this.options.width);
		this.drawLabels();
	},
	
	empty: function() {
		this.xmax = this.options.xmax;
		this.xmin = this.options.xmin;
		this.ymax = this.options.ymax;
		this.ymin = this.options.ymin;
		this.zmax = this.options.zmax;
		this.zmin = this.options.zmin;
		this.addBubble(this.xmax, this.ymax, this.zmax, [0, 0, 0], '');
		delete this.bubbles;
		this.bubbles = new Array;
		this.redraw();
	}
});
