(function($) {
    'use strict';
    var tagTemplate = function(groups){
        // var tagAllDiv = $('#tags .tag').first();
        var tagAllDiv = $("#tag-template").clone();
        tagAllDiv.css("display", "block");
        tagAllDiv.attr("id", "");
        var groupLabel = $("#group-template").clone();
        groupLabel.css("display", "block");
        groupLabel.attr("id", "");
        var tagListHtml = []
        // console.log(groups);
        if(groups){
            groups.forEach(function(groupData){
                var group = groupLabel.clone(true);
                group.html(groupData.name);
                tagListHtml.push(group);
                groupData.tags.forEach(function(tagData){
                    var tagDiv = tagAllDiv.clone(true);
                    var tagInput = tagDiv.find('input').first();
                    tagInput.prop('checked', false);
                    var tagLabel = tagDiv.find('label');
                    tagInput.attr("id", "tag-"+tagData.slug);
                    tagInput.attr("value", tagData.slug);
                    tagLabel.html(tagData.name);
                    tagLabel.attr('for', 'tag-'+tagData.slug);
                    tagListHtml.push(tagDiv);
                });
            })
            
        }
        return tagListHtml;
    };
    var videoTemplate = function(videosJson){
        var videoDiv = $("#video-template").clone();
        videoDiv.css("display", "flex");
        videoDiv.attr("id", "");
        var videoListHtml = [];
        videosJson.results.forEach(function(video){
            var newVideoDiv = videoDiv.clone();
            
            // title + link
            var videoLink = newVideoDiv.find(".video-link").first();
            videoLink.attr("href",video.link);
            videoLink.attr("title", video.title);
            videoLink.html(video.title);
            // image 
            var videoImg = newVideoDiv.find(".video-img").first();
            videoImg.attr("src", video.image);
            // duration
            var videoDuration = newVideoDiv.find(".duration").first();
            videoDuration.html(video.duration);
            // description
            var videoDescription = newVideoDiv.find(".description").first();
            var d = video.description.replace(/^([\s\S]{350}[^\s]*)[\s\S]*/, "$1");
            if (video.description.length > 350) {
                d +=" ...";
            }
            // console.log(d);
            videoDescription.html(d);
            // published_at
            var videoPublishedAt = newVideoDiv.find(".published-at").first();
            videoPublishedAt.html(video.published_at);
            // publisher
            var videoPublisher = newVideoDiv.find(".publisher").first();
            videoPublisher.html(video.publisher);
            // type
            var videoType = newVideoDiv.find(".type").first();
            videoType.html(video.type);
            // tags
            var videoTags = newVideoDiv.find(".tags").first();
            var tags_str = "";
            video.tags.forEach( el => {
                tags_str += el.name + " | ";
            });
            videoTags.html(tags_str.substring(0, tags_str.length-3));
            if(tags_str.length === 0){
                newVideoDiv.find(".meta-sep-tag").first().hide();
            }
            // insert video
            videoListHtml.push(newVideoDiv);
        });
        return videoListHtml;

    };
 
    /** parameters defined in html template:
     *  next_video_page,
     *  prev_video_page,
     *  order_by,
     *  video_lang,
     *  page_nr,
     *  tags_ajax_url,
     *  page_title,
     *
     **/
    var getTemplateParam = function(elementId){
        return JSON.parse(document.getElementById(elementId).textContent);
    }

    var VideoPage = function (){

        var state = {
            pagination: {
                previous: getTemplateParam('prev_video_page'),
                next: getTemplateParam('next_video_page'),
                // current: window.location.toString(),
            },
            params: {
                order_by: getTemplateParam('order_by'),
                video_lang: getTemplateParam('initial_video_lang'),
                page: getTemplateParam('page_nr'),
                tags: [],
            },
            baseUrl: location.protocol + '//' + location.host + location.pathname,
            pageTitle: page_title,
        };

        this.change = function(new_state){
            state = new_state;

        };
        this.getState = function(){
            return state;
        };
        this.load = function(){
            // console.log(state.params.tags);
            window. scrollTo(0,0);
            // hiCurrTag($("#"+state.tagId));
            return this.loadVideos(this.fullUrl());
        };
        this.fullUrl = function(){
            var url = state.baseUrl + "?" + $.param(state.params, true);
            return url;
        };
        this.resetPagination = function(){
            state.params.page = 1;
            var pagination = {
                previous : null,
                next: null,
                // current: null
            };
            state.pagination = pagination;
            $("#load-previous").hide();
        };
        this.toHistory = function(){
            history.pushState(state, state.pageTitle, state.baseUrl);
        };
        this.getVideos = function(url, fnStr){
            return $.get(url, function(data){
                // console.log(data);
                var videoHtml = videoTemplate(data);
                $("#content-body")[fnStr](videoHtml);
            }, "json");
        };


        
        //replace content body
        this.loadVideos = function(url){
            var spinner = $("#spinner")
            spinner.show();
            // $("#content-body").html("");
            return this.getVideos(url, "html").done(function(data){
                state.pagination.next = data.next;
                state.pagination.previous = data.previous;
                $("#result-count").html(data.count);
                spinner.hide();
            });
        };

        //append content body
        this.loadNextVideos = function(){
            var spinner = $("#spinner")
            spinner.show();
            return this.getVideos(state.pagination.next,
                                  "append").done(function(data){
                state.pagination.next = data.next;
                spinner.hide();
            });
        };
        //prepend content body
        this.loadPrevVideos = function(){
            var spinner = $("#spinner-top");
            spinner.show();
            return this.getVideos(state.pagination.previous,
                                  "prepend").done(function(data){
                state.pagination.previous = data.previous;
                spinner.hide();
            });
        };
        this.previous = function(){
            return state.pagination.previous;
        };
        // highlight currnt tag
        this.selectTags = function(){
            state.params.tags.forEach( 
                (element) => {
                    // console.log(element);
                    $('#tags input[value='+element+']').prop('checked', true);
                }
            );
        };
        this.updateTags = function(){
            $("#tags").html("");
            $('#spinner-tags').show();

            var tags_url = getTemplateParam("tags_ajax_url");
            var url = tags_url + '?' +  $.param(state.params, true);
            var THIS = this;
            return $.get(url, function(data){
                var tagListHtml = tagTemplate(data);
                $("#tags").html(tagListHtml);
                // connect events
                $("#tags input").each(function(){
                    $(this).change(function(e){
                        if(this.checked){
                            // console.log("check");
                            // if(this.value != 'all'){
                            //     $('#tags input#tag-all:checked').prop('checked', false);
                            // }
                            THIS.addTag(this.value);
                            // console.log('add tag '+this.value);
                            e.preventDefault();
                        }else{
                            // console.log("uncheck");
                            THIS.delTag(this.value);
                            e.preventDefault();
                        }
        
                    });
                });
            }, "json").done((data) => {
                    this.selectTags();
                    var newTags = [];
                    // remove tags from state which are not in tag list.
                    state.params.tags.forEach( (tagSlug, idx) => {
                        if( data.filter((tag) => tag.slug === tagSlug).length === 1){
                            // console.log(tagSlug + " in tags");
                            newTags.push(tagSlug);
                        }
                    });
                    state.params.tags = newTags;
                    $('#spinner-tags').hide();
            });
        };
        this.addTag = function(tagSlug){
            this.resetPagination();
            state.params.tags.push(tagSlug);
            this.toHistory();
            $("#spinner").show();
            $("#content-body").html("");
            return this.load();
        }
        this.delTag = function(tagSlug){
            this.resetPagination();
            var idx = state.params.tags.indexOf(tagSlug);
            if (idx > -1) { state.params.tags.splice(idx, 1);};
            
            this.toHistory();
            $("#spinner").show();
            $("#content-body").html("");
            return this.load();
        };
        this.changeOrder = function(orderBy){
            state.params.order_by = orderBy;
            this.resetPagination();
            this.toHistory();
            $("#spinner").show();
            $("#content-body").html("");
            return this.load();
        };
        this.changeLang = function(lang){
            state.params.video_lang = lang;
            // ?return 
            $("#spinner").show();
            $("#content-body").html("");
            this.updateTags().done(() => {
                this.resetPagination();
                this.toHistory();
                return this.load();
            });
        };
    }
    var page = new VideoPage();

    //infinite scroll
    var alreadyScrolling = false;
    $(window).scroll(function(){
        // get the bottom position
        var bottom_position = $(document).height() - ($(window).scrollTop() + $(window).height());
        // console.log(bottom_position);
        var state = page.getState();
        if(bottom_position<=800 && state.pagination.next !=null &&
           alreadyScrolling == false){
            alreadyScrolling = true;
            page.loadNextVideos().done(function(){
                alreadyScrolling = false;
            });
        }
    });
    // browser: back
    $(window).on('popstate', function (e) {
        var stateToLoad = e.originalEvent.state;
        page.change(stateToLoad);
        history.replaceState(stateToLoad, stateToLoad.pageTitle, stateToLoad.baseUrl);
        page.load();
    });		
	$( document ).ready(function() {
        page.load();
        page.updateTags();
    
		$('#filter').change(function(){
			if($(this).val() != ""){
                page.changeOrder($(this).val());
			}
		});
		$('#video_lang').change(function(){
			if($(this).val() != ""){
                page.changeLang($(this).val());
			}
		});
        // load specific page
		// remove page param from url
        var state = page.getState();
		history.replaceState(state, "Yoga Videos ", state.baseUrl);
		// initLoad.done(function() {
			if (page.previous() != null){
				var prevLink = $('#load-previous');
				prevLink.attr("href", page.previous());
				prevLink.show();
				prevLink.click(function(e) {
					page.loadPrevVideos().done(function(){
						if(page.previous() == null){
							prevLink.hide();
						};	
					});
					e.preventDefault();
				});
			};
		// });
	});
})(jQuery);
