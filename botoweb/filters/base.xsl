<xsl:stylesheet version='1.0' 
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform' 
 xmlns:boto='http://code.google.com/p/boto-web/wiki/FilterSchema'>
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
