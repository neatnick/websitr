<!DOCTYPE html>
<html lang="en">
% include('~head.tpl', title='appsWithStyle | iOS App Developer Team', description='Welcome to appsWithStyle! We are a team of iOS developers dedicated to producing apps with exceptional functionality, characterized by our own unique style.')
	<body class="main">
		% include('~header.tpl', page='home')
		<div class="content">

			<!-- this is horrible code, fix eventually -->
			<p id="passkey-description-calculator" style="position: absolute; top: 0; visibility: hidden">An easy to use app to manage all of the important passwords and accounts in your life, passKey is a must have for the mobile user. PassKey brings you the functionality you've come to expect from expertly crafted applications, along with the style that shapes our orgaization. PassKey stores all data locally so you don't have to worry about the security of your private information. All of the application's data is stored and encrypted on your phone, for your eyes only. Experience the beauty and seamless functionality of appsWithStyle's products: &nbsp;&nbsp;try passKey today!</p>
			<p id="mines-description-calculator" style="position: absolute; top: 0; visibility: hidden">Mines+ is an exciting, space-action game. With stunning three-dimensional graphics, and breathtaking fast-paced gameplay, it's a must have for those crucial moments of boredom. It's currently in the finally stages of production and will be coming to the App Store soon!</p>

			<div class="left-arrow">
				<div class="arrow-holder">
					<div class="arrow left" onclick="switchApp(this.classList)"></div>
				</div>
			</div>

			<div class="description-pane">
				<div id="passkey-description-pane" class="passkey" itemscope itemtype="http://schema.org/SoftwareApplication">
					<h1 itemprop="name">passKey</h1>
					<p itemprop="about description">An easy to use app to manage all of the important passwords and accounts in your life, passKey is a must have for the mobile user. PassKey brings you the functionality you've come to expect from expertly crafted applications, along with the style that shapes our orgaization. PassKey stores all data locally so you don't have to worry about the security of your private information. All of the application's data is stored and encrypted on your phone, for your eyes only. Experience the beauty and seamless functionality of appsWithStyle's products: &nbsp;&nbsp;try passKey today!</p>
					<div class="button-holder">
						<div class="aws-button"><a href="https://itunes.apple.com/us/app/passkey-pro/id862250764?mt=8">Learn More</a></div>
					</div>
				</div>		
				<div id="mines-description-pane" class="mines" itemscope itemtype="http://schema.org/SoftwareApplication">
					<h1 itemprop="name">Mines+</h1>
					<p itemprop="about description">Mines+ is an exciting, space-action game. With stunning three-dimensional graphics, and breathtaking fast-paced gameplay, it's a must have for those crucial moments of boredom. It's currently in the finally stages of production and will be coming to the App Store soon!</p>
				</div>
				<div id="risk-description-pane" class="risk" itemscope itemtype="http://schema.org/SoftwareApplication">
					<h1 itemprop="name">Color Conquest</h1>
					<p itemprop="about description">Color Conquest is a name that may need rethinking.  It's currently in the "we haven't started it yet" stages of production and will be coming to the App Store probably by mid 2015. </p>
				</div>
			</div>

			<div class="preview">
				<img id="passkey-preview-desktop" class="passkey desktop" src="preview-passkey.png" title="passKey" alt="passKey | appsWithStyle" height="661" width="331" />
				<img id="passkey-preview-mobile" class="passkey mobile" src="static/img/appicon-passkey.svg" title="passKey" alt="passKey | appsWithStyle" height="220" width="220" />
				<h1 class="passkey">passKey</h1>

				<img id="mines-preview-desktop" class="mines desktop" src="preview-mines.png" title="Mines+" alt="Mines+ | appsWithStyle" height="661" width="331" />
				<img id="mines-preview-mobile" class="mines mobile" src="static/img/appicon-mines.svg" title="Mines+" alt="Mines+ | appsWithStyle" height="220" width="220" />
				<h1 class="mines">Mines+</h1>
				
				<img id="risk-preview-desktop" class="risk desktop" src="preview-mines.png" title="Color Conquest" alt="Color Conquest | appsWithStyle" height="661" width="331" />
				<img id="risk-preview-mobile" class="risk mobile" src="static/img/appicon-mines.svg" title="Color Conquest" alt="Color Conquest | appsWithStyle" height="220" width="220" />
				<h1 class="risk">Color Conquest</h1>
			</div>

			<div class="right-arrow">
				<div class="arrow-holder">
					<div class="arrow right" onclick="switchApp(this.classList)"></div>
				</div>
			</div>

		</div>


		<script>
			// define apps enum and set selected app
			(function () {
				window.apps = {
					PASSKEY: 0,
					MINES:   1,
					RISK:    2
				};

				window.selectedApp = apps.PASSKEY;
				// TODO: set selected app based on url argument:
				// e.g. appswithstyle.net/mines (or appswithstyle.net/1 if i want to save that url)
				// sets it to mines
			})();

			var setApp = function (toApp) {
				$( ".passkey, .mines, .risk" ).each(function(index, el) {
					$(this).hide();
				});
				$( ".arrow" ).removeClass( "disabled" );

				switch (toApp) {
					case apps.PASSKEY:
						$( ".passkey" ).each(function(index, el) {
							$(this).show();
						});
						$( ".content" ).css('background', 'rgba(46,135,179,1)');
						$( ".arrow" ).each(function(index, el) {
							$(this).removeClass('mines-arrow risk-arrow').addClass('passkey-arrow');
						});
						$( ".left-arrow .arrow" ).addClass( "disabled" );
						break;
					case apps.MINES:
						$( ".mines" ).each(function(index, el) {
							$(this).show();
						});
						$( ".content" ).css('background', 'rgba(56,62,71,1)');
						$( ".arrow" ).each(function(index, el) {
							$(this).removeClass('passkey-arrow risk-arrow').addClass('mines-arrow');
						});
						$( ".right-arrow .arrow" ).addClass( "disabled" );
						break;
					case apps.RISK:
						$( "risk" ).each(function(index, el) {
							$(this).show();
						});
						break;
					default:
						$( ".passkey" ).each(function(index, el) {
							$(this).show();
						});
						break;
				}

				window.selectedApp = toApp;
				$( window ).trigger('resize');
			};

			var switchApp = function (classList) {
				if (classList.contains('disabled')) return;
				if ( $( ".content" ).width() >= 800 ) {
					if (classList.contains("right")) {
						var left = $( "body" ).width() - ($( ".right-arrow" ).width() + $( ".left-arrow" ).width());
						$( ".right-arrow>.arrow-holder" ).animate({
							'left': -left}, 600,
							function() {
								if (selectedApp == apps.PASSKEY) setApp(apps.MINES);
							});
						$( ".right-arrow>.arrow-holder" ).animate({ 'left': 0 }, 600);
					} else if (classList.contains("left")) {
						var width = $( ".left-arrow>.arrow-holder" ).width();
						var newWidth = $( "body" ).width() - $( ".left-arrow" ).width();
						$( ".left-arrow>.arrow-holder" ).animate({
							'width': newWidth}, 600,
							function() {
								if (selectedApp == apps.MINES) setApp(apps.PASSKEY);
							});
						$( ".left-arrow>.arrow-holder" ).animate({ 'width': width }, 600);
					}
				} else {
					if (classList.contains("right")) {
						if (selectedApp == apps.PASSKEY) setApp(apps.MINES);
					} else if (classList.contains("left")) {
						if (selectedApp == apps.MINES) setApp(apps.PASSKEY);
					}
				}
			};


			$(document).ready(function () {
				setApp(selectedApp, selectedApp);

				$(window).resize(function(event) {
					var width = $( ".content" ).width();
					var height = $( ".content" ).height();
					$( ".preview" ).removeClass( "mobile desktop" );
					if (width < 465 /*|| height < 465*/) {
						$( "img.passkey.mobile" ).attr({ height: 110, width: 110 });
						$( "img.mines.mobile"   ).attr({ height: 110, width: 110 });
					} else {
						$( "img.passkey.mobile" ).attr({ height: 220, width: 220 });
						$( "img.mines.mobile"   ).attr({ height: 220, width: 220 });
					}
					if (width < 800) {
						$( ".description-pane" ).css('height', $( "body" ).height() - ($( ".left-arrow" ).offset().top + 
							$( ".left-arrow" ).height() + $( ".button-holder" ).height()));
						$( "#passkey-description-pane > p" ).css('height', $( "#passkey-description-calculator" ).height() + 32);
						$( "#mines-description-pane > p" ).css('height', $( "#mines-description-calculator" ).height() + 32);
					} else {
						$( ".description-pane" ).css('height', 'auto');
						$( "#passkey-description-pane > p" ).css('height', 'auto');
						$( "#mines-description-pane > p" ).css('height', 'auto');
					}
					if (height < 658 || width < 800) {
						$( ".preview" ).addClass( "mobile" );
						switch (selectedApp) {
							case apps.PASSKEY:
								$( ".passkey.desktop" ).each(function(index, el) {
									$(this).hide();
								});
								$( ".passkey.mobile" ).each(function(index, el) {
									$(this).show();
								});
								break;
							case apps.MINES:
								$( ".mines.desktop" ).each(function(index, el) {
									$(this).hide();
								});
								$( ".mines.mobile" ).each(function(index, el) {
									$(this).show();
								});
								break;
							case apps.RISK:
								$( ".risk.desktop" ).each(function(index, el) {
									$(this).hide();
								});
								$( ".risk.mobile" ).each(function(index, el) {
									$(this).show();
								});
								break;
						}
					} else {
						$( ".preview" ).addClass( "desktop" );
						switch (selectedApp) {
							case apps.PASSKEY:
								$( ".passkey.desktop" ).each(function(index, el) {
									$(this).show();
								});
								$( ".passkey.mobile" ).each(function(index, el) {
									$(this).hide();
								});
								break;
							case apps.MINES:
								$( ".mines.desktop" ).each(function(index, el) {
									$(this).show();
								});
								$( ".mines.mobile" ).each(function(index, el) {
									$(this).hide();
								});
								break;
							case apps.RISK:
								$( ".risk.desktop" ).each(function(index, el) {
									$(this).show();
								});
								$( ".risk.mobile" ).each(function(index, el) {
									$(this).hide();
								});
								break;
						}
					}
				}).trigger('resize');

				// trigger resize event on orientation change
				$( window ).on( "orientationchange", function( event ) {
					$( window ).trigger( "resize" ); 

					// work around (change eventually)
					$( ".preview" ).css('width', $( "body" ).width() - ($( ".left-arrow" ).width() + $( ".right-arrow" ).width()));
					window.setTimeout(function () {
						$( ".preview" ).css('width', 'auto');
					}, 100);
				});
			});


/** GOOGLE ANALYTICS ****************************************************************************************************************/
			(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
			(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
			m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
			})(window,document,'script','//www.google-analytics.com/analytics.js','ga');
			ga('create', 'UA-52705756-1', 'auto');
			ga('send', 'pageview');
		</script>
	</body>
</html>