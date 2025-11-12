<?php
/**
 * Simple Channel 44 TV Live Stream Shortcode
 * Add this to your theme's functions.php file
 */

function channel44_live_stream($atts) {
    $stream_url = isset($atts['url']) ? esc_url_raw($atts['url']) : '';
    if (empty($stream_url)) {
        return '<p>Usage: [channel44_live url="http://69.167.167.129:8088/hls/YOUR-STREAM-KEY.m3u8"]</p>';
    }
    
    return '<video id="channel44-video" controls width="100%" style="max-width:100%;height:auto;background:#000;" autoplay muted>
        <source src="' . esc_url($stream_url) . '" type="application/x-mpegURL">
    </video>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        var video = document.getElementById("channel44-video");
        var videoSrc = "' . esc_js($stream_url) . '";
        if (Hls.isSupported()) {
            var hls = new Hls();
            hls.loadSource(videoSrc);
            hls.attachMedia(video);
        } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
            video.src = videoSrc;
        }
    </script>';
}
add_shortcode('channel44_live', 'channel44_live_stream');

