$(document).ready(function() {
    /* Add a [>>>] button on the top-right corner of code samples to hide
     * the >>> and ... prompts and the output and thus make the code
     * copyable. */
    const div = $('.highlight');
    const pre = div.find('pre');

    // get the styles from the current theme
    pre.parent().parent().css('position', 'relative');
    const hide_text = 'Hide the prompts and output';
    const show_text = 'Show the prompts and output';
    const border_width = pre.css('border-top-width');
    const border_style = pre.css('border-top-style');
    const border_color = pre.css('border-top-color');
    const button_styles = {
        'cursor': 'pointer', 'position': 'absolute', 'top': '0', 'right': '0',
        'border-color': border_color, 'border-style': border_style,
        'border-width': border_width, 'color': border_color, 'text-size': '75%',
        'font-family': 'monospace', 'padding-top': '0.2em', 'padding-right': '0.2em',
        'border-radius': '0 3px 0 0'
    };

    // create and add the button to all the code blocks that contain >>>
    div.each(function() {
        const jthis = $(this);
        if (jthis.find('.gp').length > 0) {
            const button = $('<span class="copybutton">&gt;&gt;&gt;</span>');
            button.css(button_styles);
            button.attr('title', hide_text);
            button.data('hidden', 'false');
            jthis.prepend(button);
        }
        // tracebacks (.gt) contain bare text elements that need to be
        // wrapped in a span to work with .nextUntil() (see later)
        jthis.find('pre:has(.gt)').contents().filter(function() {
            return ((this.nodeType === 3) && (this.data.trim().length > 0));
        }).wrap('<span>');
    });

    // define the behavior of the button when it's clicked
    $('.copybutton').click(function(e){
        e.preventDefault();
        const button = $(this);
        if (button.data('hidden') === 'false') {
            // hide the code output
            button.parent().find('.go, .gp, .gt').hide();
            button.next('pre').find('.gt').nextUntil('.gp, .go').css('visibility', 'hidden');
            button.css('text-decoration', 'line-through');
            button.attr('title', show_text);
            button.data('hidden', 'true');
        } else {
            // show the code output
            button.parent().find('.go, .gp, .gt').show();
            button.next('pre').find('.gt').nextUntil('.gp, .go').css('visibility', 'visible');
            button.css('text-decoration', 'none');
            button.attr('title', hide_text);
            button.data('hidden', 'false');
        }
    });
});
