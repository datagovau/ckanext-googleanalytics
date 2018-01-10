header_code = """
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','%s');</script>
"""

footer_code = """
<script type="text/javascript" src="%s"></script>
"""

download_style = """
<style type="text/css">
   span.downloads-count {
   font-size: 0.9em;
   }
</style>
"""
