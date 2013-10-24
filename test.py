import prosodic as p
xml="""
<?xml version="1.0" encoding="UTF-8"?>
<maryxml xmlns="http://mary.dfki.de/2002/MaryXML" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.5" xml:lang="en-US">
	<p>
		<voice name="cmu-slt-hsmm">
			<s>
				<prosody pitch="+5%" range="+20%">
					<phrase>
						<t g2p_method="lexicon" ph="' { n d" pos="CC">
And
<syllable ph="{ n d" stress="1"><ph p="{"/><ph p="n"/><ph p="d"/></syllable>
</t>
						<t accent="L+H*" g2p_method="rules" ph="' k A - l m i" pos="JJ">
calmy
<syllable accent="L+H*" ph="k A" stress="1"><ph p="k"/><ph p="A"/></syllable>
<syllable ph="l m i"><ph p="l"/><ph p="m"/><ph p="i"/></syllable>
</t>
						<t accent="L+H*" g2p_method="lexicon" ph="' b EI" pos="NN">
bay
<syllable accent="L+H*" ph="b EI" stress="1"><ph p="b"/><ph p="EI"/></syllable>
</t>
						<t pos=",">
,
</t>
						<boundary breakindex="4" tone="H-L%"/>
					</phrase>
				</prosody>
				<prosody pitch="-5%" range="-20%">
					<phrase>
						<t g2p_method="lexicon" ph="' A n" pos="IN">
on
<syllable ph="A n" stress="1"><ph p="A"/><ph p="n"/></syllable>
</t>
						<mtu orig="th'one">
							<t g2p_method="lexicon" ph="' T @U n" pos="DT">
thone
<syllable ph="T @U n" stress="1"><ph p="T"/><ph p="@U"/><ph p="n"/></syllable>
</t>
						</mtu>
						<t accent="!H*" g2p_method="lexicon" ph="' s AI d" pos="NN">
side
<syllable accent="!H*" ph="s AI d" stress="1"><ph p="s"/><ph p="AI"/><ph p="d"/></syllable>
</t>
						<t g2p_method="lexicon" ph="' S E l - t r= d" pos=".">
sheltered
<syllable ph="S E l" stress="1"><ph p="S"/><ph p="E"/><ph p="l"/></syllable>
<syllable ph="t r= d"><ph p="t"/><ph p="r="/><ph p="d"/></syllable>
</t>
						<boundary breakindex="5" tone="L-L%"/>
					</phrase>
				</prosody>
			</s>
		</voice>
	</p>
</maryxml>

"""

t=p.Text(xml)
print t.lines()
print t.parse()