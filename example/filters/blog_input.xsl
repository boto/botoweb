<xsl:stylesheet version='1.0' 
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform' >

	<xsl:param name="user_id" select="'unknown'"/>

	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
	<xsl:template match="property[@name='author']">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<object class="boto_web.resources.user.User">
				<xsl:attribute name="id"><xsl:value-of select="$user_id"/></xsl:attribute>
			</object>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
