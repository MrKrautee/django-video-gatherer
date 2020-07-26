(function($) {
    'use strict';
    // template tag
    // Handlebars.registerHelper('truncwords', function(text, length) {
    //     var words = text.split(" ");
    //     var new_text = text;
    //     if (words.length > length){
    //         new_text = "";
    //         for (var i = 0; i <= length; i++) {
    //            new_text += words[i] + " ";
    //         }  
    //         new_text = new_text.trim() + "..."          
    //     }
    //     return new_text;
    // });
    // insert data into template
    // var videoTemplate = function(data) {
    //     var source = document.getElementById("video-template").innerHTML;
    //     var template = Handlebars.compile(source);
    //     var html = template(data);
    //     return html;
    // };
    // var tagTemplate = function(data, baseUrl){
    //     var tags = {tags: data, baseUrl: baseUrl};
    //     var source = document.getElementById("tag-template").innerHTML;
    //     var template = Handlebars.compile(source);
    //     return template(tags);
    // };
    var tagTemplate = function(data){
        var tagInput = $('#tag-all');
        // ?? why losing margin after clone ??
        // tagInput.attr("style", "margin-right: 4px;");
        var tagAllDiv = tagInput.parent().clone(true);
        var baseUrl = tagInput.attr("href");
        var tagListHtml = []
        tagListHtml.push(tagAllDiv);
        data.forEach(function(tagData){
            var tagDiv = tagAllDiv.clone(true);
            var tagInput = tagDiv.find('#tag-all');
            var tagLabel = tagDiv.find('label');
            tagInput.attr("href", baseUrl+tagData.slug);
            // tagInput.attr("name", tagData.name);
            tagInput.attr("id", "tag-"+tagData.slug);
            tagLabel.html(tagData.name);
            tagLabel.attr('for', 'tag-'+tagData.slug);
            tagListHtml.push(tagDiv);
            // $("#tags").append(tag);

        });

        // var tagAll = $('#tag-all').clone(true);
        // // ?? why losing margin after clone ??
        // tagAll.attr("style", "margin-right: 4px;");
        // var baseUrl = tagAll.attr("href");
        // // $("#tags").html(tagAll);
        // var tagListHtml = []
        // tagListHtml.push(tagAll);
        // data.forEach(function(tagData){
        //     var tag = tagAll.clone(true);
        //     tag.attr("href", baseUrl+tagData.slug);
        //     tag.attr("name", tagData.name);
        //     tag.attr("id", "tag-"+tagData.slug);
        //     tag.html(tagData.name);
        //     tagListHtml.push(tag);
        //     // $("#tags").append(tag);

        // });
        return tagListHtml;
    };
    var videoTemplate = function(videosJson){
        var videoDiv = $("#content-body").children().first().clone();
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
            videoDescription.html(video.description);
            // published_at
            var videoPublishedAt = newVideoDiv.find(".published-at").first();
            videoPublishedAt.html(video.published_at);
            // publisher
            var videoPublisher = newVideoDiv.find(".publisher").first();
            videoPublisher.html(video.publisher);
            // type
            var videoType = newVideoDiv.find(".type").first();
            videoType.html(video.type);
            // ? tags
            // insert video
            videoListHtml.push(newVideoDiv);
        });
        return videoListHtml;

    };
    // highlight currnt tag
    function hiCurrTag(tagElement){
        $("#tags > a").each(function(){
            $(this).attr("class", "badge badge-secondary");
        });
        tagElement.attr("class", "badge badge-warning")
    };

    var VideoPage = function (){

        var state = {
            pagination: {
                previous: JSON.parse(document.getElementById('prev_video_page').textContent),
                next: JSON.parse(document.getElementById('next_video_page').textContent),
                // current: window.location.toString(),
            },
            params: {
                order_by: order_by,
                video_lang: video_lang,
                page: page_nr,
                tags: [],
            },
            baseUrl: location.protocol + '//' + location.host + location.pathname,
            tagId: tag_id,
            pageTitle: page_title,
        };

        this.change = function(new_state){
            state = new_state;

        };
        this.getState = function(){
            return state;
        };
        this.load = function(){
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
                var videoHtml = videoTemplate(data);
                $("#content-body")[fnStr](videoHtml);
            }, "json");
        };

        this.updateTags = function(){
            var url = "/rest/tags";
            return $.get(url, function(data){
                var tagListHtml = tagTemplate(data);
                $("#tags").html(tagListHtml);
                // hiCurrTag($("#"+state.tagId));
                console.log("tags update: "+data);
                console.log(data);
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
        this.loadByTag = function(tagSlug, tagId){
            this.resetPagination();
            // state.baseUrl = tagUrl;
            state.tagId = tagId;
            state.params.tags.push(tagSlug);
            this.toHistory();
            return this.load();
        };
        this.addTag = function(tagSlug){
            this.resetPagination();
            state.params.tags.push(tagSlug);
            this.toHistory();
            return this.load();
        }
        this.delTag = function(tagSlug){
            this.resetPagination();
            var idx = state.params.tags.indexOf(tagSlug);
            if (idx > -1) { state.params.tags.splice(idx, 1);};
            this.toHistory();
            return this.load();
        }

        this.changeOrder = function(orderBy){
            state.params.order_by = orderBy;
            this.resetPagination();
            this.toHistory();
            return this.load();
        };
        this.changeLang = function(lang){
            state.params.video_lang = lang;
            this.resetPagination();
            this.toHistory();
            return this.load();
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
        // load content 
		//var initLoad = page.load();
		
		// $('#language').change(function(){
        //     $(this).parents("form").submit();
		// });
		// $('#spinner').css("display", "block");
		// tags
		$("#tags input").each(function(){
			$(this).change(function(e){
                if(this.checked){
                    console.log("check");
                    page.addTag(this.value);
                    e.preventDefault();
                }else{
                    console.log("uncheck");
                    page.delTag(this.value);
                    e.preventDefault();
                }

			});
		});
		$('#filter').change(function(){
			if($(this).val() != ""){
                page.changeOrder($(this).val());
			}
		});
		$('#video_lang').change(function(){
			if($(this).val() != ""){
                page.changeLang($(this).val()).done(function(){
                    page.updateTags();
                });
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
