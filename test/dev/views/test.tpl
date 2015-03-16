<!DOCTYPE html>
<html lang="en">
% include('head.tpl', title='appsWithStyle | iOS App Developer Team', description='Welcome to appsWithStyle! We are a team of iOS developers dedicated to producing apps with exceptional functionality, characterized by our own unique style.')
	<body>
		<div class="overlay"></div>
		<div class="test"></div>
		<script type="text/javascript">
			(function () {
				var size = 70;
				var orientation = "";
				var wnum, hnum;

				var flipById = function (id) {
					document.getElementById(id).classList.toggle('flip');
					if (id % wnum == wnum-1) return;
					window.setTimeout(function () {
						flipById(id+1);
					}, 25);
				};

				var waitWithId = function (id, wait) {
					window.setTimeout(function () {
						flipById(id);
					}, wait);
				};

				$(window).resize(function(event) { //TODO: Debounce resize events?
					wnum = Math.floor($( ".test" ).width()/size);
					hnum = Math.floor($( ".test" ).height()/size);
					$( ".test" ).empty();
					for (var i = 0; i < wnum*hnum; i++) {
						$( ".test" ).append('<div id="'+ i +'" class="flip-container '+ orientation +'"><div class="flipper"><div class="front"></div><div class="back"></div></div></div>');
					};
					$( ".flip-container" ).width($( ".test" ).width()/wnum);
					$( ".flip-container" ).height($( ".test" ).height()/hnum);
					for (var n = wnum*(hnum - 1); n < wnum*hnum; n++) {
						$("#" + n).height(size*1.5); //height doesnt always line up for some reason
					}
					/*
					$( ".overlay" ).css('z-index', '-100');
					$( ".test>*" ).mouseleave(function(event) {
						this.classList.toggle('flip');
						window.setTimeout($.proxy(function () {
							this.classList.toggle('flip');
						}, this), 1000);
					});
					*/
				}).trigger('resize');

				$( ".overlay" ).click(function(event) {
					orientation = (orientation) ? "" : "flip";
					for (var i = 0; i < hnum; i++) {
						//flipById(i*wnum);
						waitWithId(i*wnum, 50*i);
					};
				});
			})();
		</script>
	</body>
</html>