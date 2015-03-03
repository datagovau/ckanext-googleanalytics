// Add Google Analytics Event Tracking to resource download links.
this.ckan.module('google-analytics', function(jQuery, _) {
  return {
    options: {
      googleanalytics_resource_prefix: ''
    },
    initialize: function() {
      jQuery('a.resource-url-analytics').on('click', function() {
          var resource_url = encodeURIComponent(jQuery(this).prop('href'));
          if (resource_url) {
            ga('send', 'event', 'Resource', 'Download', resource_url);
          }
      });
        jQuery('a.searchpartnership-url-analytics').on('click', function() {
            var dataset_url = encodeURIComponent(jQuery(this).prop('href'));
            var dataset_portal = encodeURIComponent(jQuery(this).attr('data-portal'));
            if (dataset_url) {
                ga('send', 'event', 'Search Partnership Redirect', dataset_portal, dataset_url);
            }
        });
    }
  }
});
