var autoprefixer = require('autoprefixer');
var postcss = require('postcss');
process.stdin.on('readable', () => {
	const css = process.stdin.read();
	if (css !== null) {
		postcss([autoprefixer ]).process(css).then(function(result) {process.stdout.write(result.css);});
	}
});
