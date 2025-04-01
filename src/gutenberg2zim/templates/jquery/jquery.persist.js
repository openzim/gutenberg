/*
	jquery-persist 201203*pike

	persist form values in cookies

	example usage:

		$('input,select,textarea').persist(options);

		$('input,select,textarea').unpersist(options);

	options

		context 	: 'def',		// a context or namespace for each field
		replace		: true,			// replace existing field contents if any
		cookie		: 'jqpersist',	// cookies basename
		path		: '/',			// cookie path
		domain		: null,			// cookie domain
		expires		: null,			// cookie expiry (eg 365)

*/



jQuery.fn.persist = function(options) {

	options = jQuery.extend({}, jQuery.persist.defaults, options);
	return jQuery(this).each(function() {
		var name = $(this).attr('name');
		var val =jQuery.persistedValue(name,options);
		if(val) {
			switch(this.tagName.toLowerCase()) {
				case  'input':
					switch($(this).attr('type')) {
						case 'submit':
					                // Do nothing
                  				        break;
						case 'radio':
							// if we can replace anything or there are no checked radio buttons
							if (options['replace']||$(this).parents('form').eq(0).find('input[name="'+name+'"]:checked').size()==0) {
								$(this).parents('form').eq(0)
									.find('input[name="'+name+'"]').each(function() {
									this.checked = ($(this).val()==val);
								});
							}
							break;
						case 'checkbox':
							var vals = val.split(jQuery.persist.arrsep);
							$(this).parents('form').eq(0)
								.find('input[name="'+name+'"]').each(function() {
								// if we can replace this value or it was checked by itself
								this.checked = ((jQuery.inArray($(this).val(),vals)!=-1)||(this.checked&&!options['replace']));
							});
							break;
						default:
							// if we can replace it or it is empty or 0
							if (options['replace']||!$(this).val()) {
								$(this).val(val);
							}
					}
					break;
				case 'select':
					if ($(this).attr('multiple')) {
						var vals = val.split(jQuery.persist.arrsep);
						$(this).children('option').each(function() {
							// if we can replace this value or it was selected by itself
							this.selected = ((jQuery.inArray($(this).val(),vals)!=-1)||(this.selected&&!options['replace']));
						});
					} else {
						// if we can replace it or it is empty or 0
						if (options['replace']||!$(this).val()) {
							$(this).val(val);
						}
					}
					break;
				default:
					// if we can replace it or it is empty or 0
					if (options['replace']||!$(this).val()) {
						$(this).val(val);
					}
			}
		}
	}).on('change.persist', function(){
		var name = $(this).attr('name');
		switch(this.tagName.toLowerCase()) {
			case  'input':
				switch($(this).attr('type')) {
					case "checkbox":
						var vals = [];
						$(this).parents('form').eq(0)
							.find('input[name="'+name+'"]').each(function() {
							if (this.checked) vals.push($(this).val());
						});
						jQuery.persistValue(name,vals.join(jQuery.persist.arrsep),options);
						break;
					default:
						jQuery.persistValue(name, $(this).val(), options);
				}
				break;
			case "select":
				if ($(this).attr('multiple')) {
					var vals = [];
					$(this).children('option').each(function() {
						if (this.selected) vals.push($(this).val());
					});
					jQuery.persistValue(name,vals.join(jQuery.persist.arrsep),options);
				} else {
					jQuery.persistValue(name, $(this).val(), options);
				}
				break;
			default:
				jQuery.persistValue(name, $(this).val(), options);
		}
	});
}

jQuery.fn.unpersist = function(options) {
	options = jQuery.extend({}, jQuery.persist.defaults, options);
	$(this).each(function() {
		var name = $(this).attr('name');
		jQuery.persistValue(name,null,options);
	}).off('change.persist');
	return $(this);
}

jQuery.persistValue = function (key, value, options) {

	options = jQuery.extend({}, jQuery.persist.defaults, options);
	var ctx = options['context'];

	if (!jQuery.persist.keys.length) {
		if (!jQuery.persistInit(options)) return false;
	}
	var idx = jQuery.inArray(ctx+jQuery.persist.ctxsep+key,jQuery.persist.keys);
	if (idx!=-1) {
		if (value === null || value === undefined) {
			// remove value
			if (jQuery.persist.debug) console.log('unpersist '+key);
			jQuery.persist.keys.splice(idx,1);
			jQuery.persist.vals.splice(idx,1);
		} else {
			if (jQuery.persist.debug) console.log('persist '+key+':'+value);
			jQuery.persist.vals[idx]=value;
		}
	} else {
		if (!(value === null || value === undefined)) {
			if (jQuery.persist.debug) console.log('add persist '+key+':'+value);
			jQuery.persist.keys.push(ctx+jQuery.persist.ctxsep+key);
			jQuery.persist.vals.push(value);
		}
	}
	if (jQuery.persist.keys.length) {
		// store keys/vals
		jQuery.cookie(options.cookie+'_keys',jQuery.persist.keys.join(jQuery.persist.elmsep),options);
		jQuery.cookie(options.cookie+'_vals',jQuery.persist.vals.join(jQuery.persist.elmsep),options);
	} else {
		// remove the whole cookie
		options['expire']=null;
		jQuery.cookie(options.cookie+'_keys','',options);
		jQuery.cookie(options.cookie+'_vals','',options);
	}
}


jQuery.persistedValue = function(key,options) {

	options = jQuery.extend({}, jQuery.persist.defaults, options);
	var ctx = options['context'];

	if (!jQuery.persist.keys.length) {
		if (!jQuery.persistInit(options)) return false;
	}

	var idx = jQuery.inArray(ctx+jQuery.persist.ctxsep+key,jQuery.persist.keys);
	if (idx!=-1) {
		if (jQuery.persist.debug) console.log('persisted '+key+':'+ jQuery.persist.vals[idx]);
		return jQuery.persist.vals[idx];
	} else {
		if (jQuery.persist.debug) console.log('persisted '+key+': nop');
		return null; //undefined
	}

}

jQuery.persistInit = function(options) {
	if (jQuery.persist.debug) console.log('persist init ');
	options = jQuery.extend({}, jQuery.persist.defaults, options);
	var skeys = jQuery.cookie(options.cookie+'_keys') || '';
	var svals = jQuery.cookie(options.cookie+'_vals') || '';
	jQuery.persist.keys = skeys.split(jQuery.persist.elmsep);
	jQuery.persist.vals = svals.split(jQuery.persist.elmsep);
	if (jQuery.persist.keys.length!=jQuery.persist.vals.length) {
		// this should never happen
		alert('persist error - erasing');
		options['expire']=null;
		jQuery.cookie(options.cookie+'_keys',null,options);
		jQuery.cookie(options.cookie+'_vals',null,options);
		jQuery.persist.keys = [];
		jQuery.persist.vals = [];
		return false;
	}
	if (jQuery.persist.debug) console.log(jQuery.persist.keys);
	if (jQuery.persist.debug) console.log(jQuery.persist.vals);
	return true;
}

jQuery.persist = {
	debug	: true,
	defaults: {
		context 	: 'def',		// a context or namespace for each field
		replace		: true,			// replace existing field contents if any
		cookie		: 'jqpersist',	// cookies basename
		path		: '/',			// cookie path
		domain		: null,			// cookie domain
		expires		: null			// cookie expiry (eg 365)
	},
	elmsep		: '##',
	ctxsep		: '::',
	arrsep		: '//',
	keys		: [],
	vals		: []
};
