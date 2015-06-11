@route('/', method='POST')
def api():
    if request.POST.get("v") == 'vendetta': 
        return """\
Evey:  Who are you?
   V:  Who? Who is but the form following the function of what, and what 
       I am is a man in a mask.
Evey:  Well I can see that.
   V:  Of course you can. I'm not questioning your powers of observation; 
       I'm merely remarking upon the paradox of asking a masked man who 
       he is.
Evey:  Oh. Right.
   V:  But on this most auspicious of nights, permit me then, in lieu of 
       the more commonplace sobriquet, to suggest the character of this 
       dramatis persona.
   V:  Voila! In view, a humble vaudevillian veteran cast vicariously as 
       both victim and villain by the vicissitudes of Fate. This visage, 
       no mere veneer of vanity, is a vestige of the vox populi, now 
       vacant, vanished. However, this valourous visitation of a bygone 
       vexation stands vivified and has vowed to vanquish these venal and 
       virulent vermin vanguarding vice and vouchsafing the violently 
       vicious and voracious violation of volition! The only verdict is 
       vengeance; a vendetta held as a votive, not in vain, for the value 
       and veracity of such shall one day vindicate the vigilant and the 
       virtuous. Verily, this vichyssoise of verbiage veers most verbose, 
       so let me simply add that it's my very good honour to meet you and 
       you may call me V.
"""

    return load_root()