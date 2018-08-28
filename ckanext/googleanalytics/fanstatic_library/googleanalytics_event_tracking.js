// Add Google Analytics Event Tracking to resource download links.
this.ckan.module('google-analytics', function(jQuery, _) {
  return {
    options: {
      googleanalytics_resource_prefix: ''
    },
    initialize: function() {
      if (jQuery("meta[property='dataset']")[0].content) {
        ga('send', 'event', 'Dataset view by Publisher', jQuery("meta[name='DCTERMS.Creator']")[0].content, jQuery("meta[property='dataset']")[0].content);
      }
      jQuery('a.resource-url-analytics').on('click', function() {
          var resource_url = encodeURIComponent(jQuery(this).prop('href'));
          if (resource_url) {
            ga('send', 'event', 'Resource', 'Download', resource_url);
            ga('send', 'event', 'Download by Dataset', jQuery("meta[property='dataset']")[0].content, resource_url);
            ga('send', 'event', 'Download by Publisher', jQuery("meta[name='DCTERMS.Creator']")[0].content, resource_url);
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
